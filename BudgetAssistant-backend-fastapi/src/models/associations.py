"""Association tables for many-to-many relationships."""

from sqlmodel import Field, SQLModel


class UserBankAccountLink(SQLModel, table=True):
    """Association table for User <-> BankAccount many-to-many relationship."""

    __tablename__ = "user_bank_account_link"

    user_id: int | None = Field(default=None, foreign_key="user.id", primary_key=True)
    bank_account_number: str | None = Field(
        default=None, foreign_key="bankaccount.account_number", primary_key=True
    )


class UserCounterpartyLink(SQLModel, table=True):
    """Association table for User <-> Counterparty many-to-many relationship."""

    __tablename__ = "user_counterparty_link"

    user_id: int | None = Field(default=None, foreign_key="user.id", primary_key=True)
    counterparty_name: str | None = Field(
        default=None, foreign_key="counterparty.name", primary_key=True
    )


class UserRuleSetLink(SQLModel, table=True):
    """Association table for User <-> RuleSetWrapper many-to-many relationship."""

    __tablename__ = "user_ruleset_link"

    user_id: int | None = Field(default=None, foreign_key="user.id", primary_key=True)
    ruleset_id: int | None = Field(
        default=None, foreign_key="rulesetwrapper.id", primary_key=True
    )


# Export the link tables for use in relationships
user_bank_account_link = UserBankAccountLink
user_counterparty_link = UserCounterpartyLink
user_ruleset_link = UserRuleSetLink

