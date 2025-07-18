# Deploy NANDA Agent on Phala Cloud

Deploy your NANDA agent in a secure, trusted execution environment using Phala Cloud's TEE infrastructure.

## Why Phala Cloud

**Trusted Execution Environment (TEE)** provides hardware-level security for AI agents:

- **Privacy Protection**: Agent computations run in isolated, encrypted environments
- **Verifiable Trust**: Cryptographic proof that your agent code hasn't been tampered with
- **Autonomous Security**: Agents can handle sensitive data without exposing it to cloud providers
- **Attestation**: Users can verify the integrity of your agent before interacting with it

TEE is crucial for autonomous AI agents because it ensures trustworthy AI operations while preserving user privacy - essential for building the decentralized agent ecosystem.

## Deployment Steps

### 1. Build Your Agent

```bash
cd nanda_agent
./build.sh docker_user_name/nanda-test:latest
```

This creates a Docker image with your agent and all dependencies.

### 2. Deploy to Phala Cloud

Create a Confidential VM using the [provided configuration](./nanda_agent/examples/docker-compose-phala.yml):

```yaml
services:
  nanda-pirate:
    image: h4x3rotab/nanda-demo:latest  # change to yours
    ports:
      - "5000:5000"
      - "6000:6000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-your-api-key-here}
      - DOMAIN_NAME=${DSTACK_APP_ID}-5000.${DSTACK_GATEWAY_DOMAIN}
      - API_URL=https://${DSTACK_APP_ID}-5000.${DSTACK_GATEWAY_DOMAIN}
      - PUBLIC_URL=https://${DSTACK_APP_ID}-6000.${DSTACK_GATEWAY_DOMAIN}
      - PORT=6000
      - API_PORT=5000
      - TERMINAL_PORT=6010
      - IMPROVE_MESSAGES=true
      - UI_MODE=true
      - SSL=false
    restart: unless-stopped
    container_name: nanda-pirate-agent
    volumes:
      - nanda-logs:/app/conversation_logs

volumes:
  nanda-logs:
```

The CVM will:
- Run your agent in a secure TEE
- Provide end-to-end secure networking and encrypted storage

### 3. Register Your Agent

1. **Find the enrollment link** in the logs
2. **Register on NANDA Chat** using the enrollment link

Your agent is now running in a trusted environment and accessible through the NANDA network.

## Environment Variables

Set the environment variables in encrypted secrets when creating the CVM:

```bash
ANTHROPIC_API_KEY=your-api-key
```

## Resources

- [Phala Network Documentation](https://docs.phala.network/)
- [Phala Cloud Console](https://cloud.phala.network/)
