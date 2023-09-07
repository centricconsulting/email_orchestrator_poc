import os
from dotenv import load_dotenv
from monday import MondayClient

load_dotenv()


class MondayManager:
    def __init__(self, token):
        self.client = MondayClient(token)
        self.fields_cache = {} # Cache for groups
        self.board_id_cache = {}  # Cache for board IDs
        self.group_id_cache = {}  # Cache for group IDs

    def get_board_id_by_name(self, board_name):
        if board_name in self.board_id_cache:
            return self.board_id_cache[board_name]

        boards = self.client.boards.fetch_boards()
        for board in boards['data']['boards']:
            if board['name'] == board_name:
                self.board_id_cache[board_name] = board['id']
                return board['id']
        return None

    def get_group_id_by_name(self, board_id, group_name):
        cache_key = (board_id, group_name)
        if cache_key in self.group_id_cache:
            return self.group_id_cache[cache_key]

        groups = self.client.groups.get_groups_by_board(board_id)
        for group in groups['data']['boards'][0]['groups']:
            if group['title'] == group_name:
                self.group_id_cache[cache_key] = group['id']
                return group['id']
        return None

    def get_fields_for_board(self, board_id):
        if board_id not in self.fields_cache:
            fields = self.client.boards.fetch_columns_by_board_id(board_id)
            self.fields_cache[board_id] = fields['data']['boards'][0]['columns']
        return self.fields_cache[board_id]

    def get_field_by_title(self, board_id, field_name):
        fields = self.get_fields_for_board(board_id)
        for field in fields:
            if field['title'] == field_name:
                return field['id']
        return None

    def create_item(self, board_id, group_id, item_name, column_values):
        keys_to_replace = list(column_values.keys())
        for col_value in keys_to_replace:
            field_id = self.get_field_by_title(board_id, col_value)
            self._replace_key(column_values, col_value, field_id)
        return self.client.items.create_item(board_id=board_id, group_id=group_id,
                                             item_name=item_name, column_values=column_values)

    @staticmethod
    def _replace_key(original_dict, old_key, new_key):
        if old_key in original_dict:
            original_dict[new_key] = original_dict.pop(old_key)
        return original_dict
