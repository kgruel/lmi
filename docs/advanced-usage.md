# Advanced Usage

Explore advanced features such as scripting, environment switching, and automation with **lmi**.

## 1. Scripting with lmi

lmi is designed for automation and scripting. You can use it in shell scripts or CI pipelines:

```sh
for env in $(ls ~/.config/lmi/env/*.env | xargs -n1 basename | sed 's/\.env$//'); do
  lmi -e "$env" <service_group> <action> [options]
done
```

## 2. Automating Workflows

- Use environment variables and config files to automate authentication and config selection.
- Pipe input data to commands that support `--file -`:
  ```sh
  cat data.json | lmi <service_group> <action> --file -
  ```
- Capture output in JSON for further processing:
  ```sh
  lmi <service_group> <action> --output json | jq .
  ```

## 3. Environment Switching

- Quickly switch between environments using the `-e <env_name>` flag:
  ```sh
  lmi -e staging <service_group> <action>
  lmi -e prod <service_group> <action>
  ```
- Use different `.env` files for each environment to manage credentials and endpoints securely. 