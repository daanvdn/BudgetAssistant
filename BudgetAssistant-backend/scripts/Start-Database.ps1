#print pwd
Write-Output "Current directory: $( Get-Location )"

function Get-DotEnv($filePath)
{
    Get-Content $filePath | ForEach-Object {
        $line = $_.Trim()
        if ($line -match '^\s*#' -or -not $line)
        {
            return
        } # Skip comments and empty lines
        $name, $value = $line -split '=', 2
        if ($name -and $value)
        {
            [System.Environment]::SetEnvironmentVariable($name.Trim(),$value.Trim(), "Process")
        }
    }
}

# Call function with the path to your .env file
Get-DotEnv ".\.env"

$POSTGRES_USER = $Env:POSTGRES_USER
$POSTGRES_PASSWORD = $Env:POSTGRES_PASSWORD
$POSTGRES_DB = $Env:POSTGRES_DB
#log the user and prod db
Write-Output "User: $POSTGRES_USER"
Write-Output "Password: $POSTGRES_PASSWORD"
Write-Output "Database: $POSTGRES_DB"

Write-Output "Checking if PostgreSQL container exists"
$container = docker ps -a --filter "name=postgres" --format "{{.Names}}"

if ($container -eq "postgres")
{
    Write-Output "Starting existing PostgreSQL container"
    docker start postgres
}
else
{
Write-Output "Starting new PostgreSQL docker image"
docker run -d `
  --name postgres `
  -e POSTGRES_DB=$POSTGRES_DB `
  -e POSTGRES_USER=$POSTGRES_USER `
  -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD `
  -p 5432:5432 `
  --mount type=bind,source=C:\docker-data\postgres,target=/var/lib/postgresql/data `
  postgres:latest
#-v C:\Users\daanv\Git\BudgetAssistant\BudgetAssistant-backend\init.sql:/docker-entrypoint-initdb.d/init.sql `
#
}
