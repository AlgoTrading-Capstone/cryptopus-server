from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.admin_panel.serializers import (
    AgentUploadSerializer,
    AgentActivateSerializer,
    HotSwapSerializer,
    AdminAgentSerializer,
    UpdateUserStatusSerializer,
    AdminUserSerializer,
)
from apps.admin_panel.services import AdminService
from apps.authentication.models import User


class IsAdmin(IsAuthenticated):
    """Only allow admin users."""
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role == User.Role.ADMIN
        )


class AdminAgentUploadView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        """POST /api/admin/agents/upload"""
        serializer = AgentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            agent = AdminService.upload_agent(
                admin_user=request.user,
                **serializer.validated_data,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(
            {"status": "success", "data": AdminAgentSerializer(agent).data},
            status=status.HTTP_201_CREATED,
        )


class AdminAgentsListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        """GET /api/admin/agents"""
        agents = AdminService.get_all_agents()
        return Response(
            {"status": "success", "data": AdminAgentSerializer(agents, many=True).data},
            status=status.HTTP_200_OK,
        )


class AdminAgentDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, agent_id):
        """GET /api/admin/agents/{agent_id}"""
        try:
            agent = AdminService.get_agent(agent_id=str(agent_id))
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {"status": "success", "data": AdminAgentSerializer(agent).data},
            status=status.HTTP_200_OK,
        )


class AdminAgentActivateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, agent_id):
        """POST /api/admin/agents/{agent_id}/activate"""
        serializer = AgentActivateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            agent = AdminService.activate_agent(agent_id=str(agent_id))
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"status": "success", "data": AdminAgentSerializer(agent).data},
            status=status.HTTP_200_OK,
        )


class AdminAgentDeactivateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, agent_id):
        """POST /api/admin/agents/{agent_id}/deactivate"""
        try:
            agent = AdminService.deactivate_agent(agent_id=str(agent_id))
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"status": "success", "data": AdminAgentSerializer(agent).data},
            status=status.HTTP_200_OK,
        )


class AdminHotSwapView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        """POST /api/admin/agents/hot-swap"""
        serializer = HotSwapSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = AdminService.hot_swap(
                from_agent_id=str(serializer.validated_data["from_agent_id"]),
                to_agent_id=str(serializer.validated_data["to_agent_id"]),
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class AdminSystemStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        """GET /api/admin/system/stats"""
        data = AdminService.get_system_stats()
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class AdminSystemHealthView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        """GET /api/admin/system/health"""
        data = AdminService.get_system_health()
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class AdminUsersListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        """GET /api/admin/users"""
        users = AdminService.get_all_users()
        return Response(
            {"status": "success", "data": AdminUserSerializer(users, many=True).data},
            status=status.HTTP_200_OK,
        )


class AdminUserDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, user_id):
        """GET /api/admin/users/{user_id}"""
        try:
            user = AdminService.get_user(user_id=str(user_id))
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {"status": "success", "data": AdminUserSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class AdminUserStatusView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, user_id):
        """PATCH /api/admin/users/{user_id}/status"""
        serializer = UpdateUserStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = AdminService.update_user_status(
                user_id=str(user_id),
                account_status=serializer.validated_data["account_status"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {"status": "success", "data": AdminUserSerializer(user).data},
            status=status.HTTP_200_OK,
        )