from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
)


def get_db_type_id():
    db_type_ids = exec_test_command(
        BASE_CMDS["databases"]
        + [
            "types",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    return db_type_ids[0] if db_type_ids else None


def get_engine_id():
    engine_ids = exec_test_command(
        BASE_CMDS["databases"]
        + [
            "engines",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    return engine_ids[0] if engine_ids else None
