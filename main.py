import time
import asyncio
import aiofiles
import statistics
import numpy as np
import asyncclick as click

from yarl import URL
from typing import List, Dict
from aiohttp import ClientSession
from aiohttp.client_exceptions import InvalidURL, ClientResponseError


@click.command()
@click.option(
    "--file-path",
    "-f",
    type=click.Path(exists=True),
    help="""Insert with '--file-path={path}' or '-f={path}' path of file that
         you want to read requests response time from.""",
)
async def command_reader(file_path: str):
    try:
        request_times: List = []

        async with aiofiles.open(file_path, mode="r") as f:
            async with ClientSession(raise_for_status=True) as client:
                async for line in f:
                    time_taken = await request_maker(client, line)
                    request_times.append(time_taken)

                metrics: Dict = calculate_metrics(request_times)
                click.echo(
                    click.style(
                        f"Time metrics -> Mean: {metrics.get('mean')}, Median: {metrics.get('median')}, 90th percentile: {metrics.get('90percentile')}.",  # noqa: E501
                        fg="cyan",
                    )
                )

    except (FileNotFoundError, SystemError):
        click.echo(click.style(f"Invalid file path {file_path}!", fg="red"))
        click.echo(
            click.style("Please provide a valid full file path!", fg="red")
        )


async def request_maker(client: ClientSession, url: str) -> float:
    try:
        start_time = time.time()
        async with client.get(URL(threat_url(url), encoded=True)) as response:
            await response.text()
            end_time = time.time()
            taken: float = end_time - start_time

            click.echo(
                click.style(
                    f"Time taken: {taken}, status: {response.status}",
                    fg="green",
                )
            )

        return taken

    except InvalidURL as ex:
        click.echo(click.style(f"Invalid url: {ex.url}", fg="red"))
    except ClientResponseError as ex:
        click.echo(
            click.style(
                f"Error at GET {ex.request_info.url}, status: {ex.status}",
                fg="red",
            )
        )


def threat_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""

    if url[-1] == "/":
        url = url[:-1]

    return url


def calculate_metrics(response_times: List[float]) -> Dict:
    response_times = [res_time for res_time in response_times if res_time]
    return {
        "median": statistics.median(response_times),
        "mean": sum(response_times) / len(response_times),
        "90percentile": np.percentile(response_times, 90),
    }


if __name__ == "__main__":
    click.clear()
    click.secho("🛠  Request Timer CLI 🛠", fg="blue")
    command_reader(_anyio_backend="asyncio")
