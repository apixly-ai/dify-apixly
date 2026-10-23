from tools import base


class CreateVideoTool(base.MediaTool):
    catalog_kind = "video"

    def execute(self, client, parameters):
        return client.create_video(
            base.selected_model(parameters),
            parameters.get("prompt"),
            base.model_parameters(parameters, ("seconds", "resolution", "aspect_ratio")),
        )
