import asyncio
import base64
import json
from os import environ
from pathlib import Path
from datetime import datetime
from enum import StrEnum, auto
from time import perf_counter_ns
from typing import Optional, List, Union, Tuple, AsyncGenerator

from openai import AsyncOpenAI
from tqdm.asyncio import tqdm

from typing import Never

JOB_ID = environ.get("JOB_ID", environ.get("SLURM_JOB_ID", environ.get("SLURM_JOBID", None)))
DATE = datetime.now().strftime('%Y%m%d_%H%M%S')

def assert_never(arg: Never) -> Never:
    raise AssertionError("Expected code to be unreachable")


class ImageFormat(StrEnum):
    png = auto()
    jpeg = auto()
    jpg = auto()
    webp = auto()
    gif = auto()

    @classmethod
    def from_path(cls, path: Path) -> Optional["ImageFormat"]:
        suffix = path.suffix.lower()
        match suffix:
            case ".png":
                return cls.png
            case ".jpeg":
                return cls.jpeg
            case ".jpg":
                return cls.jpg
            case ".webp":
                return cls.webp
            case ".gif":
                return cls.gif
            case _:
                return None

    def base64_prefix(self):
        match self:
            case ImageFormat.png:
                return "data:image/png;base64,"
            case ImageFormat.jpeg:
                return "data:image/jpeg;base64,"
            case ImageFormat.jpg:
                return "data:image/jpeg;base64,"
            case ImageFormat.webp:
                return "data:image/webp;base64,"
            case ImageFormat.gif:
                return "data:image/gif;base64,"
            case _:
                assert_never(self)

    def glob_pattern(self):
        match self:
            case ImageFormat.png:
                return "*.png"
            case ImageFormat.jpeg:
                return "*.jpeg"
            case ImageFormat.jpg:
                return "*.jpg"
            case ImageFormat.webp:
                return "*.webp"
            case ImageFormat.gif:
                return "*.gif"
            case _:
                assert_never(self)


class ImageFile:
    def __init__(self, path: Path):
        self.path = path
        self.format = ImageFormat.from_path(path)
        if self.format is None:
            raise ValueError(f"Unsupported image format for file {path}")

        self.stem = path.stem
        self.suffix = path.suffix.lower()
        self.extension = self.suffix[1:]  # remove the dot

        self.base64_prefix = self.format.base64_prefix()

    def open(self):
        return self.path.open("rb")

    def as_base64(self):
        with self.open() as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode("utf-8")
            return f"{self.base64_prefix}{base64_data}"

    @property
    def xml_name(self):
        return self.path.with_suffix(".xml").name

    def __str__(self):
        return self.path.as_posix()


async def connexion_test(
        client: AsyncOpenAI,
) -> bool:
    try:
        await client.models.list()
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False


async def wait_for_connection(
        client: AsyncOpenAI,
        timeout: int = 120,
        interval: int = 5,
) -> bool:
    start_time = perf_counter_ns()
    while True:
        try:
            assert await connexion_test(client), "Connection test failed"
            print("Connection successful")
            return True
        except Exception as e:
            elapsed_time = (perf_counter_ns() - start_time) / 1e9
            if elapsed_time >= timeout:
                print(f"Connection failed after {elapsed_time:.2f} seconds: {e}")
                return False
            print(f"Connection failed, retrying in {interval} seconds... ({elapsed_time:.2f}s elapsed)")
            await asyncio.sleep(interval)


async def do_one_image(
        client: AsyncOpenAI,
        model: str,
        prompt: str,
        file: ImageFile,
) -> Tuple[str, ImageFile]:
    response = await client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": file.as_base64()},
                ],
            }
        ],
    )

    return response.output_text, file


async def do_one_image_file_api(
        client: AsyncOpenAI,
        model: str,
        prompt: str,
        file: ImageFile,
) -> Tuple[str, ImageFile]:
    with file.open() as f:
        up_file = client.files.create(
            file=f,
            purpose="vision",
        )

    response = await client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_file", "file_id": (await up_file).id},
                    {"type": "input_text", "text": prompt},
                ],
            }
        ],
    )

    return response.output_text, file


async def do_multiple_images(
        client: AsyncOpenAI,
        model: str,
        prompt: str,
        files: List[ImageFile],
        concurrency: int,
) -> AsyncGenerator[Tuple[str, ImageFile], None]:
    semaphore = asyncio.Semaphore(concurrency)

    async def process_image(file: ImageFile) -> Tuple[str, ImageFile]:
        async with semaphore:
            return await do_one_image(client, model, prompt, file)

    tasks = [asyncio.create_task(process_image(file)) for file in files]
    for task in tqdm(tasks, total=len(files)):
        yield await task


def find_images(
        input_dir: Union[str, Path, None] = None,
        image_formats: Optional[List[Union[ImageFormat]]] = None,
        glob_prefix: Optional[str] = None,
) -> Tuple[List[ImageFile], dict]:
    if input_dir is None:
        input_dir = environ.get("CHURROLESS_INPUT_DIR", "examples/mini_ballard")
    input_dir = Path(input_dir)
    assert input_dir.is_dir(), f"Input path {input_dir} is not a directory"

    if glob_prefix is None:
        glob_prefix = environ.get("CHURROLESS_GLOB_PREFIX", "")

    if image_formats is None:
        image_formats = environ.get("CHURROLESS_IMAGE_FORMATS", "png").split(",")
        image_formats = [ImageFormat(fmt.strip()) for fmt in image_formats]
    assert len(image_formats) > 0, "At least one image format must be specified"
    assert all(isinstance(fmt, ImageFormat) for fmt in image_formats), "All image formats must be valid ImageFormat values"

    patterns = [f"{glob_prefix}{fmt.glob_pattern()}" for fmt in image_formats]

    files = set()
    for pattern in patterns:
        files |= {
            ImageFile(path) for path in input_dir.glob(pattern) if path.is_file()
        }

    return list(files), {
        "input_dir": input_dir.as_posix(),
        "image_formats": [fmt.value for fmt in image_formats],
        "glob_prefix": glob_prefix,
    }


async def main(
        input_files: List[ImageFile],
        prompt: Optional[str] = None,
        output_dir: Union[str, Path, None] = None,
        model: Optional[str] = None,
        concurrency: Optional[int] = None,
        host_url: Optional[str] = None,
        api_key: Optional[str] = None,
) -> dict:
    if prompt is None:
        prompt = environ.get(
            "CHURROLESS_PROMPT",
            "Transcribe the entirety of this historical document to XML format."
        )
    assert isinstance(prompt, str), "Prompt must be a string"

    if model is None:
        model = environ.get("CHURROLESS_MODEL", "mradermacher/churro-3B-GGUF:Q4_K_M")
    assert isinstance(model, str), "Model must be a string"

    assert isinstance(input_files, list) and len(input_files) > 0, "Input files must be a non-empty list"
    assert all(isinstance(f, ImageFile) for f in input_files), "All input files must be of type ImageFile"

    if concurrency is None:
        concurrency = int(environ.get("CHURROLESS_CONCURRENCY", 5))
    assert isinstance(concurrency, int) and concurrency > 0, "Concurrency must be a positive integer"

    if host_url is None:
        host_url = environ.get("CHURROLESS_HOST_URL", "http://localhost:8080")
    assert isinstance(host_url, str) and host_url.startswith("http"), "Host URL must be a valid URL string"

    if api_key is None:
        api_key = environ.get("CHURROLESS_KEY", "dummy")
    assert isinstance(api_key, str) and len(api_key) > 0, "API key must be a non-empty string"

    if output_dir is None:
        output_dir = environ.get(
            "CHURROLESS_OUTPUT_DIR",
            Path.cwd() / "outputs" / f"churroless_output{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    assert output_dir.is_dir(), f"{output_dir} is not a directory"

    client = AsyncOpenAI(
        base_url=host_url,
        api_key=api_key,
    )
    await wait_for_connection(client)

    now = datetime.now()
    now_pf = perf_counter_ns()

    print(f"""\
    Starting with the following parameters:
    Job ID: {JOB_ID or "N/A"}
    Model: {model}
    Host URL: {host_url}
    Output directory: {output_dir}
    Concurrency: {concurrency}
    Number of files: {len(input_files)}
    Prompt: {prompt}
    
    At: {now.isoformat()}  
    
    IDs:
        JOB_ID: {environ.get("JOB_ID")}
        SLURM_JOB_ID: {environ.get("SLURM_JOB_ID")}
        SLURM_JOBID: {environ.get("SLURM_JOBID")}
    """)

    async for result_xml, result_image in do_multiple_images(
            client=client,
            model=model,
            prompt=prompt,
            files=input_files,
            concurrency=concurrency,
    ):
        with (output_dir / result_image.xml_name).open(mode="w", encoding="utf-8") as f:
            f.write(result_xml)

    later_now = datetime.now()
    later_now_pf = perf_counter_ns()
    time_spent = (later_now_pf - now_pf)

    print(f"Finished at : {later_now.isoformat()}, took {time_spent / 1e9:.2f} seconds")

    return {
        "output_dir": output_dir.as_posix(),
        "input_files": [str(f) for f in input_files],
        "num_files_in": len(input_files),
        "num_files_out": len(list(output_dir.iterdir())),

        "host_url": host_url,
        "model": model,
        "prompt": prompt,

        "concurrency": concurrency,
        "start_time": now.isoformat(),
        "time_spent": time_spent,
        "end_time": later_now.isoformat(),
        "time_spent_seconds": time_spent / 1e9,

        "job_id": JOB_ID or "N/A"
    }


if __name__ == "__main__":
    input_dir = Path("examples/mini_ballard")
    image_formats = [
        ImageFormat.png,
        # ImageFormat.jpeg,
        # ImageFormat.jpg,
        # ImageFormat.webp,
        # ImageFormat.gif,
    ]
    glob_prefix = ""

    prompt = Path("prompts/v4").read_text(encoding="utf-8")
    model = None
    output_dir = (
            Path.cwd()
            / "outputs"
            / f"churroless_output_{f'job-{JOB_ID}' if JOB_ID is not None else f'date-{DATE}'}"
    )
    concurrency = None
    host_url = None
    api_key = None

    input_files, params_find = find_images(
        input_dir=input_dir,
        image_formats=image_formats,
        glob_prefix=glob_prefix,
    )

    params_run = asyncio.run(
        main(
            prompt=prompt,
            model=model,
            input_files=input_files,
            output_dir=output_dir,
            concurrency=concurrency,
            host_url=host_url,
            api_key=api_key,
        )
    )

    params = {
        **params_find,
        **params_run,
    }

    output_dir = Path(params_run["output_dir"])

    with (output_dir / "params.json").open(mode="w", encoding="utf-8") as f:
        json.dump(params, f, indent=4, ensure_ascii=False)
