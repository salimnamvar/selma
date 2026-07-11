from pydantic import BaseModel, ConfigDict


class DomainValueObject(BaseModel):
    """Base for all Policy Doctrine value objects.

    Enforces immutability and strict schema validation. All domain
    value objects inherit from this to eliminate repetitive config.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
