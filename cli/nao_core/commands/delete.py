from typing import Annotated

import httpx
from cyclopts import Parameter

from nao_core.tracking import track_command
from nao_core.ui import UI, ask_confirm


@track_command("delete")
def delete(
    project: Annotated[str, Parameter(help="Name of the project to delete", name=["--project", "-p"])],
    url: Annotated[str, Parameter(help="Remote nao instance URL")],
    api_key: Annotated[str, Parameter(help="API key for authentication", name=["--api-key", "-k"])],
    yes: Annotated[bool, Parameter(help="Skip the confirmation prompt", name=["--yes", "-y"])] = False,
) -> None:
    """Permanently delete a project from a remote nao instance."""
    if not yes and not ask_confirm(
        f"Permanently delete project [cyan]{project}[/cyan] from [cyan]{url}[/cyan]?", default=False
    ):
        UI.print("Delete cancelled.")
        return

    delete_url = f"{url.rstrip('/')}/api/deploy"

    UI.print(f"\n[dim]Deleting {project}...[/dim]")
    try:
        response = httpx.delete(
            delete_url,
            headers={"Authorization": f"Bearer {api_key}"},
            params={"project": project},
            timeout=30.0,
        )
    except httpx.ConnectError:
        UI.error(f"Could not connect to {url}")
        UI.print("[dim]Check the URL and ensure the nao instance is running.[/dim]")
        return
    except httpx.TimeoutException:
        UI.error("Request timed out")
        return

    if response.status_code == 401:
        UI.error("Authentication failed. Check your API key.")
        return

    if response.status_code == 404:
        UI.error(f"No project named [cyan]{project}[/cyan] found")
        return

    if response.status_code != 200:
        UI.error(f"Delete failed ({response.status_code})")
        try:
            error = response.json().get("error", response.text)
        except Exception:
            error = response.text
        UI.print(f"[red]{error}[/red]")
        return

    result = response.json()
    UI.success(f"Project [cyan]{result.get('projectName', project)}[/cyan] deleted")
    UI.print(f"[dim]Project ID: {result.get('projectId')}[/dim]")
