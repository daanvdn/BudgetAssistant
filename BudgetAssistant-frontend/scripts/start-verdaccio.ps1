$container = docker ps -a --filter "name=verdaccio" --format "{{.Names}}"
if ($container -eq "verdaccio")
{
    #check if the container is already running
    $is_running = docker inspect -f '{{.State.Running}}' verdaccio
    if ($is_running -eq "true")
    {
        Write-Output "Verdaccio container is already running"
        exit
    }
    else
    {
        Write-Output "Starting existing Verdaccio container"
        docker start verdaccio
    }
}
else
{
    Write-Output "Starting new Verdaccio docker image"
    docker run -d `
      --name verdaccio `
      -p 4873:4873 `
      --mount type=bind,source=C:\docker-data\verdaccio,target=/verdaccio/storage `
      verdaccio/verdaccio:latest
}