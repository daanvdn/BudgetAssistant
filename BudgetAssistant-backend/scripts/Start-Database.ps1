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
Get-DotEnv ".\pybackend\.env"

$MY_SQL_USER = $Env:MY_SQL_USER
$MY_SQL_PASSWORD = $Env:MY_SQL_PASSWORD
$MY_SQL_PROD_DB = $Env:MY_SQL_PROD_DB
$MYSQL_ROOT_PASSWORD = $Env:MYSQL_ROOT_PASSWORD
#log the user and prod db
Write-Output "User: $MY_SQL_USER"
Write-Output "Password: $MY_SQL_PASSWORD"
Write-Output "Database: $MY_SQL_PROD_DB"

Write-Output "Checking if MariaDB container exists"
$container = docker ps -a --filter "name=mariadb" --format "{{.Names}}"

if ($container -eq "mariadb")
{
    Write-Output "Starting existing MariaDB container"
    docker start mariadb
}
else
{
Write-Output "Starting new MariaDB docker image"
docker run -d `
  --name mariadb `
  -e MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD `
  -e MYSQL_DATABASE=$MY_SQL_PROD_DB `
  -e MYSQL_USER=$MY_SQL_USER `
  -e MYSQL_PASSWORD=$MY_SQL_PASSWORD `
  -p 3306:3306 `
  --mount type=bind,source=C:\docker-data\mariadb,target=/var/lib/mysql `
  mariadb:latest
#-v C:\Users\daanv\Git\BudgetAssistant\BudgetAssistant-backend\init.sql:/docker-entrypoint-initdb.d/init.sql `
#
}