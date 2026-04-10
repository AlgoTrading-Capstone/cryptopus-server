from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.agent.serializers import (
    AgentSerializer,
    AgentMetricsQuerySerializer,
    AgentPlotsQuerySerializer,
)
from apps.agent.services import AgentService


class ActiveAgentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/agent/active"""
        try:
            agent = AgentService.get_active_agent()
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {"status": "success", "data": AgentSerializer(agent).data},
            status=status.HTTP_200_OK,
        )


class ActiveAgentMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/agent/active/metrics"""
        serializer = AgentMetricsQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = AgentService.get_active_agent_metrics(
                range=serializer.validated_data["range"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class ActiveAgentPlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/agent/active/plots"""
        serializer = AgentPlotsQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = AgentService.get_active_agent_plots(
                range=serializer.validated_data["range"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class ActiveAgentExplanationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/agent/active/explanation"""
        data = AgentService.get_active_agent_explanation()
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class AgentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/agent/status"""
        data = AgentService.get_agent_runtime_status()
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)