# BrainK D-030 Network Boundary

This deployment boundary keeps database control-plane traffic private and allows only the minimum runtime egress needed for execution evidence.

## Ingress
- 443/tcp: public application/runtime edge.
- 5432/tcp: private/internal clients only. Never expose PostgreSQL on a public interface.
- 22/tcp: explicit administrative allowlist only.
- Established/related traffic and essential ICMP/ICMPv6 are allowed.

## Egress
- 53/tcp+udp: DNS.
- 443/tcp: GitHub/Google/authorised verification and deployment services.
- 5432/tcp: private address space only.
- 123/udp: NTP.
- Default deny for everything else.

## Database
- SCRAM-SHA-256 authentication.
- Application role: `braink_runtime`.
- Database: `braink_control`.
- pg_hba.conf rejects all unmatched IPv4/IPv6 sources.
- Replace broad RFC1918 examples with exact production subnets before activation.

## Verification law
A firewall file committed to Git is IMPLEMENTED only. DEPLOYED requires loading the rules on the target host and reading back the active ruleset. FUNCTIONING requires successful permitted flows and failed denied flows. VERIFIED requires a distinct assessor to repeat those observations.
