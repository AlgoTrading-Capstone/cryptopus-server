import uuid
from django.db import models
from apps.authentication.models import User


class Agent(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    version = models.TextField()
    s3_model_path = models.TextField() #actual model file path in s3
    s3_metadata_path = models.TextField() #path in s3 where we store metadata like normalization profile, strategy set hash etc. This is to ensure that metadata and model file are stored together and can be easily retrieved.
    normalization_profile = models.TextField() #must match the normalization profile used during training. This is required to ensure that the input data is normalized in the same way as the training data.
    strategy_set_hash = models.TextField() #hash of the strategy set used during training. This is required to ensure that the same strategy set is used during inference. We can use this hash to retrieve the strategy set from s3 and load it into memory during inference.
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.INACTIVE,
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.RESTRICT, #this block deletion entirely if there are agents referencing the user. We want to keep the agent records intact even if the user is deleted, but we don't want to allow deletion of users who have uploaded agents without first reassigning or deleting those agents.
        related_name="uploaded_agents",
    )
    activated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "agents"

    def __str__(self):
        return f"{self.name} v{self.version} - {self.status}"