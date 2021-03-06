from flask import jsonify
from flask_restful import Resource, request, current_app
from flask_swagger import swagger

from server.services.settings_service import SettingsService
from server.services.messaging.smtp_service import SMTPService
from server.services.users.authentication_service import token_auth, tm


class SystemDocsAPI(Resource):
    """
    This Resource provides a simple endpoint for flask-swagger to generate the API docs,
    https://github.com/gangverk/flask-swagger
    """

    def get(self):
        """
        Generates Swagger UI readable JSON
        ---
        tags:
          - system
        definitions:
            - schema:
                id: GeoJsonPolygon
                properties:
                    type:
                        type: string
                        default: Polygon
                    coordinates:
                        type: array
                        items:
                            type: number
                            default: [[-4.0237,56.0904],[-3.9111,56.1715],[-3.8122,56.0980],[-4.0237,56.0904]]
            - schema:
                id: GeoJsonMultiPolygon
                properties:
                    type:
                        type: string
                        default: MultiPolygon
                    coordinates:
                        type: array
                        items:
                            type: number
                            default: [[[-4.0237,56.0904],[-3.9111,56.1715],[-3.8122,56.0980],[-4.0237,56.0904]]]
            - schema:
                id: ProjectInfo
                properties:
                    locale:
                        type: string
                        default: en
                    name:
                        type: string
                        default: Thinkwhere Project
                    shortDescription:
                        type: string
                        default: Awesome little project
                    description:
                        type: string
                        default: Awesome little project and a little bit more
                    instructions:
                        type: string
                        default: Complete the tasks
                    perTaskInstructions:
                       type: string
                       default: Use Thinkwhere Imagery Only
            - schema:
                id: GeoJsonFeature
                properties:
                    type:
                        type: string
                        default: Feature
                    geometry:
                        schema:
                              $ref: "#/definitions/GeoJsonMultiPolygon"
                    properties:
                        type: object
                        properties:
                            x:
                                type: integer
                                default: 2402
                            y:
                                type: integer
                                default: 1736
                            zoom:
                                type: integer
                                default: 12
                            isSquare:
                                type: boolean
                                default: true
            - schema:
                id: ValidatedTask
                properties:
                    taskId:
                        type: integer
                        default: 1
                    status:
                        type: string
                        default: VALIDATED
                    comment:
                        type: string
                        default: Nice work :)
            - schema:
                id: ResetTask
                properties:
                    taskId:
                        type: integer
                        default: 1
                    comment:
                        type: string
                        default: Work in progress
            - schema:
                id: ProjectTeams
                properties:
                    teamId:
                        type: integer
                        default: 1
                    role:
                        type: string
                        default: MAPPER
            - schema:
                id: TeamMembers
                properties:
                    userName:
                        type: string
                        default: the_node_less_traveled
                    function:
                        type: string
                        default: MANAGER


        """
        swag = swagger(current_app)
        swag["info"]["title"] = "Tasking Manager backend API"
        swag["info"]["description"] = "API endpoints for the backend"
        swag["info"]["version"] = "2.0.0"

        return jsonify(swag)


class SystemHeartbeatAPI(Resource):
    """
    /api/health-check
    """

    def get(self):
        """
        Simple health-check, if this is unreachable load balancers should be configures to raise an alert
        ---
        tags:
          - system
        produces:
          - application/json
        responses:
          200:
            description: Service is Healthy
        """
        return {"status": "healthy"}, 200


class SystemLanguagesAPI(Resource):
    def get(self):
        """
        Gets all supported languages
        ---
        tags:
          - system
        produces:
          - application/json
        responses:
            200:
                description: Supported Languages
            500:
                description: Internal Server Error
        """
        try:
            languages = SettingsService.get_settings()
            return languages.to_primitive(), 200
        except Exception as e:
            error_msg = f"Languages GET - unhandled error: {str(e)}"
            current_app.logger.critical(error_msg)
            return {"Error": "Unable to fetch supported languages"}, 500


class SystemContactAdminRestAPI(Resource):
    @tm.pm_only(False)
    @token_auth.login_required
    def post(self):
        """
        Send an email to the system admin
        ---
        tags:
          - system
        produces:
          - application/json
        parameters:
          - in: header
            name: Authorization
            description: Base64 encoded session token
            required: true
            type: string
            default: Token sessionTokenHere==
          - in: body
            name: body
            required: true
            description: JSON object with the data of the message to send to the system admin
            schema:
                properties:
                    name:
                        type: string
                        default: The name of the sender
                    email:
                        type: string
                        default: The email of the sender
                    content:
                        type: string
                        default: The content of the message
        responses:
          201:
            description: Email sent successfully
          400:
              description: Invalid Request
          401:
              description: Unauthorized - Invalid credentials
          403:
              description: Forbidden
          500:
            description: A problem occurred
        """
        try:
            data = request.get_json()
            message = """New contact from {} <{}> (UID: {}).
                <p>{}</p>
                """.format(
                data.get("name"),
                data.get("email"),
                tm.authenticated_user_id,
                data.get("content"),
            )
            SMTPService._send_message(
                current_app.config["EMAIL_FROM_ADDRESS"],
                "Tasking Manager Contact",
                message,
                message,
            )
            return {"Success": "Email sent"}, 201
        except Exception as e:
            error_msg = f"Application GET API - unhandled error: {str(e)}"
            current_app.logger.critical(error_msg)
            return {"Error": "Unable to fetch application keys"}, 500
