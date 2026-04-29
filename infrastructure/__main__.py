"""A Python Pulumi program"""
import base64

from dotenv import dotenv_values

import pulumi
import ediri_vultr as vultr

CLOUD_INIT = """#cloud-config
ssh_pwauth: false
allow_public_ssh_keys: true
disable_root: true

packages:
  - ufw
  - iproute2-ss
  - bind-tools
  - git
  - uv

package_update: true
package_upgrade: true

users:
  - default
  - name: {username}
    groups: wheel
    ssh_authorized_keys:
      - {ssh_public_key}

write_files:
  - path: /etc/doas.d/10-root.conf
    content: |
      permit root as {username}
    owner: root:root
    permissions: '0644'
  - path: /etc/doas.d/20-wheel.conf
    content: |
      permit nopass :wheel
      permit nopass {username}
    owner: root:root
    permissions: '0644'
  - path: /etc/ssh/sshd_config.d/00-{username}.conf
    content: |
      Protocol 2
      PermitRootLogin no
      PubkeyAuthentication yes
      PasswordAuthentication no
      PermitEmptyPasswords no
      ChallengeResponseAuthentication no
      KbdInteractiveAuthentication no
      HostbasedAuthentication no
      IgnoreRhosts yes
      MaxAuthTries 3
      MaxSessions 5
      LoginGraceTime 30
      PrintMotd no
      PermitUserEnvironment no
      SyslogFacility AUTH
      LogLevel VERBOSE
      ClientAliveInterval 300
      ClientAliveCountMax 3
      TCPKeepAlive no 
      AllowUsers {username}
      AllowTcpForwarding yes
    owner: root:root
    permissions: '0600'
  - path: /etc/init.d/garybot
    encoding: b64
    content: {openrc_service_script}
    owner: root:root
    permissions: '0755'
  - path: /tmp/.env
    encoding: b64
    content: {dot_env_file}
    owner: root:root
    permissions: '0600'

runcmd:
  - ufw delete allow ssh
  - ufw allow from {home_ip} to any port 22 proto tcp
  - ufw allow from 10.0.0.0/24 to any proto tcp # move vpc address to a config file or something
  - ufw default deny incoming
  - ufw default allow outgoing
  - rc-service sshd restart
  - git clone {repo_url} /home/{username}/{repo_name}
  - mv /tmp/.env /home/{username}/{repo_name}/.env
  - chown -R {username}:{username} /home/{username}/{repo_name}
  - chmod +x /home/{username}/{repo_name}/start.sh
  - rc-update add garybot default
  - rc-service garybot start
  - rc-service garybot status
"""


if __name__ == "__main__":
    stack_name = pulumi.get_stack()

    infra_config = dotenv_values(".env")
    vultr_region = infra_config["VULTR_REGION"]
    username = infra_config["USERNAME"]
    hostname = f"{infra_config["HOSTNAME"]}-{stack_name}"
    plan = infra_config["PLAN"]
    os_id = infra_config["OS_ID"]
    home_ip = infra_config["HOME_IP"]
    ssh_key_name = infra_config["SSH_KEY_NAME"]
    repo_name = infra_config["REPO_NAME"]
    repo_url = infra_config["REPO_URL"]

    app_config = pulumi.Config("garybot")
    app_config_dict = {
        'irc_nick': app_config.require("irc_nick"),
        'irc_server': app_config.require_secret("irc_server"),
        'irc_port': app_config.require_secret("irc_port"),
        'irc_main_channel': app_config.require_secret("irc_main_channel"),
        'irc_llm_model': app_config.require("irc_llm_model"),
        'irc_ignore_list': app_config.require_secret("irc_ignore_list"),
        'wolfram_api_key': app_config.require_secret("wolfram_api_key"),
        'odds_api_key': app_config.require_secret("odds_api_key"),
        'llm_api_key': app_config.require_secret("llm_api_key"),
        'nasa_api_key': app_config.require_secret("nasa_api_key"),
        'youtube_api_key': app_config.require_secret("youtube_api_key"),
    }
    dot_env_file = pulumi.Output.all(**app_config_dict).apply(
        lambda cfg: base64.b64encode(
            "\n".join([f"{k.upper()}={v}" for k,v in cfg.items()]).encode()
        ).decode()
    )

    with open("openrc_service_script", "r") as f:
        openrc_service_script = f.read().format(
            username=username,
            repo_name=repo_name,
        )

    # get existing ssh key
    ssh_key = vultr.get_ssh_key(
        filters=[{
            "name": "name",
            "values": [ssh_key_name]
        }]
    )

    # get existing vpc
    vpc = vultr.get_vpc(filters=[{
        "name": "description",
        "values": ["vpc-129w81st"],
    }])

    # get existing firewall group
    fwg_vpc = vultr.get_firewall_group(filters=[{
        "name": "description",
        "values": ["fwg-vpc"],
    }])

    # create instance
    user_data = pulumi.Output.format(
        CLOUD_INIT,
        ssh_public_key=ssh_key.ssh_key,
        username=username,
        home_ip=home_ip,
        repo_url=repo_url,
        repo_name=repo_name,
        openrc_service_script=base64.b64encode(openrc_service_script.encode()).decode(),
        dot_env_file=dot_env_file,
    )
    buttebot_instance = vultr.Instance(
        f"garybot-{stack_name}",
        label=hostname,
        plan=plan,
        region=vultr_region,
        firewall_group_id=fwg_vpc.id,
        hostname=hostname,
        os_id=os_id,
        vpc_ids=[vpc.id],
        ssh_key_ids=[ssh_key.id],
        user_data=user_data,
    )
