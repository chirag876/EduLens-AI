from typing import Any


def filter_none(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def has_key(key: str, data: dict[str, Any]) -> bool:
    return key in data


def has_keys(keys: list[str], data: dict[str, Any]) -> bool:
    return all(key in data for key in keys)


def has_keys_none(keys: list[str], data: dict[str, Any]) -> bool:
    return all(key in data for key in keys)


def get_value(key: str, data: dict[str, Any]) -> Any:
    return data.get(key)


def rename_key(old_name: str, new_name: str, data: dict[str, Any]) -> dict[str, Any]:
    if has_key(old_name, data):
        data[new_name] = data.pop(old_name)
    return data


def remove_keys(keys: list[str], data: dict[str, Any]) -> list[Any]:
    return [data.pop(key) for key in keys if key in data]


def snake_case_mapping(elements: dict[str, Any]) -> dict[str, Any]:
    return {key: '_'.join(key.lower().split()) for key in elements}


def switch_key_value(items: dict[str, Any]):
    return {y: x for x, y in items.items()}
