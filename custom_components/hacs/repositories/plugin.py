"""Class for plugins in HACS."""
import json
from .repository import HacsRepository, register_repository_class


@register_repository_class
class HacsPlugin(HacsRepository):
    """Plugins in HACS."""

    category = "plugin"

    def __init__(self, full_name):
        """Initialize."""
        super().__init__()
        self.information.full_name = full_name
        self.information.category = self.category
        self.information.name = full_name.split("/")[-1]
        self.content.path.local = (
            f"{self.system.config_path}/www/community/{self.information.name}"
        )

    async def validate_repository(self):
        """Validate."""
        # Run common validation steps.
        await self.common_validate()

        # Custom step 1: Validate content.
        await self.get_plugin_location()

        if self.content.path.remote is None:
            self.validate.errors.append("Repostitory structure not compliant")

        if self.content.path.remote == "release":
            self.content.single = True

        self.content.files = []
        for filename in self.content.objects:
            self.content.files.append(filename.name)

        # Handle potential errors
        if self.validate.errors:
            for error in self.validate.errors:
                if not self.common.status.startup:
                    self.logger.error(error)
        return self.validate.success

    async def registration(self):
        """Registration."""
        if not await self.validate_repository():
            return False

        # Run common registration steps.
        await self.common_registration()

    async def update_repository(self):
        """Update."""
        # Run common update steps.
        await self.common_update()

        # Get plugin objects.
        await self.get_plugin_location()

        if self.content.path.remote is None:
            self.validate.errors.append("Repostitory structure not compliant")

        if self.content.path.remote == "release":
            self.content.single = True

        self.content.files = []
        for filename in self.content.objects:
            self.content.files.append(filename.name)

    async def get_plugin_location(self):
        """Get plugin location."""
        if self.content.path.remote is not None:
            return

        possible_locations = ["dist", "release", ""]
        for location in possible_locations:
            try:
                files = []
                if location != "release":
                    objects = await self.repository_object.get_contents(
                        location, self.ref
                    )
                    for item in objects:
                        if item.name.endswith(".js"):
                            files.append(item.name)

                # Handler for plug requirement 3
                find_file_name = f"{self.information.name.replace('lovelace-', '')}.js"
                if find_file_name in files or f"{self.information.name}.js" in files:
                    # YES! We got it!
                    self.content.path.remote = location
                    self.content.objects = objects
                    self.content.files = files

            except SystemError:
                pass

    async def get_package_content(self):
        """Get package content."""
        try:
            package = await self.repository_object.get_contents("package.json")
            package = json.loads(package.content)

            if package:
                self.information.authors = package["author"]
        except Exception:
            pass