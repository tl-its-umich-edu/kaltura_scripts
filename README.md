# Kaltura scripts

Designed to support University of Michigan Kaltura services report needs. We will be adding more scripts in the future.

## Development

### Pre-requisities

The sections below provide instructions for configuring, installing, and using the application.
Depending on the environment you plan to run the application in, you may
also need to install some or all of the following:

- [Python 3.8](https://docs.python.org/3.8/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [OpenShift CLI](https://docs.openshift.com/enterprise/3.1/cli_reference/get_started_cli.html)

While performing any of the actions described below, use a terminal, text editor, or file
utility as necessary. Sample terminal commands are provided for some steps.

### Configuration

Before running the application, you will need to prepare the configuration file: `env.json` file containing key-value pairs that will be added to the environment. See the **Installation & Usage** section below for details on where the file will need to be located.

- `env.json`

  The `env.son` file serves as the primary configuration file, loading credentials for kaltura admins. A template called `env_sample.json` has been provided in
  the `config` directory. The comments before the variables in the template should describe the purpose of each; some recommended values have been provided. If you use the approach described below in **Installation & Usage - With Docker**, you can use the provided values to connect to the database managed by Docker.

The meanings of the keys and their expected values are described in the table below.

| **Key**      | **Description**                                                                                                                       |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `user_id`    | The id of the Kaltura user who will run this report script                                                                            |
| `kmcs`       | The list of Kaltura Management Consoles with associated partnerID and adminKey values                                                 |
| `ftp_server` | The ftp server with hostname, username and password information. The script will ftp the generated KMC admin csv file to this server. |

---

Create your own versions of `env.json`, and be prepared to move them to specific directories.

### Installation & Usage

#### With Docker

Before beginning, perform the following additional steps to configure the project for Docker.

1.  Build an docker image

    ```sh
    docker build -t kaltura .
    ```

2.  Run a container using the tagged image.

    ```sh
    docker run kaltura
    ```
