import abc

class CloudConnector(abc.ABC):
    """Abstract base class for cloud provider security connectors."""
    
    @abc.abstractmethod
    def scan(self, framework: str) -> list[dict]:
        """Scan cloud resources and return findings."""
        pass

    @abc.abstractmethod
    def execute_remediation(self, finding_control: str) -> dict:
        """Execute remediation for a given control and return result."""
        pass


class AWSConnector(CloudConnector):
    """Mock AWS security connector."""
    
    def scan(self, framework: str) -> list[dict]:
        control = "AWS-IAM-001"
        if framework == "HIPAA":
            control = "164.312(a)(1)"
        elif framework == "GDPR":
            control = "Art.25"
        return [
            {
                "control": control,
                "description": "AWS S3 bucket public access enabled",
                "status": "non_compliant",
                "evidence": "arn:aws:s3:::authclaw-production-data allows public read access"
            }
        ]

    def execute_remediation(self, finding_control: str) -> dict:
        return {
            "connector": "AWS",
            "control": finding_control,
            "status": "success",
            "details": "Disabled public access block on S3 bucket arn:aws:s3:::authclaw-production-data"
        }


class AzureConnector(CloudConnector):
    """Mock Azure security connector."""
    
    def scan(self, framework: str) -> list[dict]:
        control = "AZURE-SEC-002"
        if framework == "HIPAA":
            control = "164.312(e)(1)"
        elif framework == "GDPR":
            control = "Art.32"
        return [
            {
                "control": control,
                "description": "Azure SQL database without firewall rules",
                "status": "non_compliant",
                "evidence": "Resource Group: authclaw-rg, Server: authclaw-db allows 0.0.0.0/0"
            }
        ]

    def execute_remediation(self, finding_control: str) -> dict:
        return {
            "connector": "Azure",
            "control": finding_control,
            "status": "success",
            "details": "Restricted firewall rules on Azure SQL server authclaw-db to secure VNet"
        }


class GCPConnector(CloudConnector):
    """Mock GCP security connector."""
    
    def scan(self, framework: str) -> list[dict]:
        control = "GCP-IAM-003"
        if framework == "HIPAA":
            control = "164.312(d)(1)"
        elif framework == "GDPR":
            control = "Art.30"
        return [
            {
                "control": control,
                "description": "GCP Service Account with Owner permissions",
                "status": "non_compliant",
                "evidence": "Service Account authclaw-runner@gcp-project.iam.gserviceaccount.com has roles/owner"
            }
        ]

    def execute_remediation(self, finding_control: str) -> dict:
        return {
            "connector": "GCP",
            "control": finding_control,
            "status": "success",
            "details": "Revoked roles/owner and assigned roles/viewer to authclaw-runner service account"
        }
