# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import requests
from datetime import datetime

from recognizers_number import recognize_number, Culture
from recognizers_date_time import recognize_datetime

from botbuilder.core import (
    ActivityHandler,
    ConversationState,
    TurnContext,
    UserState,
    MessageFactory,
)
from botbuilder.schema import Activity
import json
from data_models import ConversationFlow, Question, UserProfile


STATUS_CODE__SUCCESS = 200


class ValidationResult:
    def __init__(
        self, is_valid: bool = False, value: object = None, message: str = None
    ):
        self.is_valid = is_valid
        self.value = value
        self.message = message

class CustomPromptBot(ActivityHandler):
    def __init__(self, conversation_state: ConversationState, user_state: UserState):
        if conversation_state is None:
            raise TypeError(
                "[CustomPromptBot]: Missing parameter. conversation_state is required but None was given"
            )
        if user_state is None:
            raise TypeError(
                "[CustomPromptBot]: Missing parameter. user_state is required but None was given"
            )

        self.conversation_state = conversation_state
        self.user_state = user_state
        self.ALLOCATION_TYPES = ['google', 'number', 'list', 'sequence', 'mass', 'template']
        self.flow_accessor = self.conversation_state.create_property("ConversationFlow")
        self.profile_accessor = self.user_state.create_property("UserProfile")
        self.user_skype_object = None
        self.user_skype_login = None
        self.auth = False

    async def on_message_activity(self, turn_context: TurnContext):
        # Get the state properties from the turn context.
        profile = await self.profile_accessor.get(turn_context, UserProfile)
        flow = await self.flow_accessor.get(turn_context, ConversationFlow)

        await self._fill_out_user_profile(flow, profile, turn_context)

        # Save changes to UserState and ConversationState
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    def update_user_object(self, user_object):
        if user_object:
            self.user_skype_object = user_object

    def update_user_login(self, user_object):
        if user_object \
                and user_object.get('from') \
                and user_object['from'].get('name') \
                and user_object != self.user_skype_login:
            self.user_skype_login = user_object['from']['name']

    def get_account_by_login(self, login):
        try:
            response = requests.post(url='http://10.0.22.62/api/v1.0',
                                     json={'id': None, 'jsonrpc': '2.0', 'method': 'account:get_list', 'params': {'filter': {'messenger': login}}})
            print('RESPONCSE,', response.json())
            if response.status_code == STATUS_CODE__SUCCESS:
                response_data = response.json()['account_list']
                print(response_data)

                if len(response_data) == 1:
                    return response_data.pop()
        except Exception as err:
            print(err)
        return None


    async def _fill_out_user_profile(
        self, flow: ConversationFlow, profile: UserProfile, turn_context: TurnContext
    ):
        user_object = dict(eval(json.dumps(Activity.serialize(turn_context.activity))))
        self.update_user_login(user_object)

        user_input = turn_context.activity.text.strip()

        # ask for name
        if flow.last_question_asked == Question.NONE:
            auth_user = self.get_account_by_login(self.user_skype_login)
            self.update_user_object(auth_user)

            if not self.user_skype_object:
                await turn_context.send_activity(
                    MessageFactory.text("We can't identify you. Please contact to support skype")
                )
            else:
                await turn_context.send_activity(
                    MessageFactory.text(f"Hello, {self.user_skype_object['name']}")
                )
            self.auth = True if self.user_skype_object else False

            if self.auth:
                flow.last_question_asked = Question.ALLOCATION

        # validate name then ask for age
        elif flow.last_question_asked == Question.ALLOCATION:
            validate_result = self._recognize_allocation(user_input)
            if not validate_result.is_valid:
                await turn_context.send_activity(
                    MessageFactory.text(validate_result.message)
                )
            else:
                profile.name = validate_result.value
                print(profile)
                await turn_context.send_activity(
                    MessageFactory.text(f"Hi {profile.name}")
                )
                await turn_context.send_activity(
                    MessageFactory.text("How old are you?")
                )
                flow.last_question_asked = Question.NONE

        # validate age then ask for date
        elif flow.last_question_asked == Question.AGE:
            validate_result = self._validate_age(user_input)
            if not validate_result.is_valid:
                await turn_context.send_activity(
                    MessageFactory.text(validate_result.message)
                )
            else:
                profile.age = validate_result.value
                await turn_context.send_activity(
                    MessageFactory.text(f"I have your age as {profile.age}.")
                )
                await turn_context.send_activity(
                    MessageFactory.text("When is your flight?")
                )
                # flow.last_question_asked = Question.DATE

        # validate date and wrap it up
        elif flow.last_question_asked == Question.DATE:
            validate_result = self._validate_date(user_input)
            if not validate_result.is_valid:
                await turn_context.send_activity(
                    MessageFactory.text(validate_result.message)
                )
            else:
                profile.date = validate_result.value
                await turn_context.send_activity(
                    MessageFactory.text(
                        f"Your cab ride to the airport is scheduled for {profile.date}."
                    )
                )
                await turn_context.send_activity(
                    MessageFactory.text(
                        f"Thanks for completing the booking {profile.name}."
                    )
                )
                await turn_context.send_activity(
                    MessageFactory.text("Type anything to run the bot again.")
                )
                flow.last_question_asked = Question.NONE

    def _recognize_allocation(self, user_input: str) -> ValidationResult:

        if not user_input:
            return ValidationResult(
                is_valid=False,
                message="Please enter a allocation type that contains an valid type of following list:\n Google;\n "
                        "Number;\n List;\n Sequence;\n Mass;\n Template List.",
            )

        if user_input.lower() in self.ALLOCATION_TYPES:
            return ValidationResult(is_valid=True, value=user_input)
        else:
            return ValidationResult(
                is_valid=False,
                message="Please enter a allocation type that contains an valid type of following list:\n Google;\n "
                        "Number;\n List;\n Sequence;\n Mass;\n Template List.",
            )

    def _validate_name(self, user_input: str) -> ValidationResult:
        if not user_input:
            return ValidationResult(
                is_valid=False,
                message="Please enter a name that contains at least one character.",
            )

        return ValidationResult(is_valid=True, value=user_input)

    def _validate_age(self, user_input: str) -> ValidationResult:
        # Attempt to convert the Recognizer result to an integer. This works for "a dozen", "twelve", "12", and so on.
        # The recognizer returns a list of potential recognition results, if any.
        results = recognize_number(user_input, Culture.English)
        for result in results:
            if "value" in result.resolution:
                age = int(result.resolution["value"])
                if 18 <= age <= 120:
                    return ValidationResult(is_valid=True, value=age)

        return ValidationResult(
            is_valid=False, message="Please enter an age between 18 and 120."
        )

    def _validate_date(self, user_input: str) -> ValidationResult:
        try:
            # Try to recognize the input as a date-time. This works for responses such as "11/14/2018", "9pm",
            # "tomorrow", "Sunday at 5pm", and so on. The recognizer returns a list of potential recognition results,
            # if any.
            results = recognize_datetime(user_input, Culture.English)
            for result in results:
                for resolution in result.resolution["values"]:
                    if "value" in resolution:
                        now = datetime.now()

                        value = resolution["value"]
                        if resolution["type"] == "date":
                            candidate = datetime.strptime(value, "%Y-%m-%d")
                        elif resolution["type"] == "time":
                            candidate = datetime.strptime(value, "%H:%M:%S")
                            candidate = candidate.replace(
                                year=now.year, month=now.month, day=now.day
                            )
                        else:
                            candidate = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

                        # user response must be more than an hour out
                        diff = candidate - now
                        if diff.total_seconds() >= 3600:
                            return ValidationResult(
                                is_valid=True,
                                value=candidate.strftime("%m/%d/%y"),
                            )

            return ValidationResult(
                is_valid=False,
                message="I'm sorry, please enter a date at least an hour out.",
            )
        except ValueError:
            return ValidationResult(
                is_valid=False,
                message="I'm sorry, I could not interpret that as an appropriate "
                "date. Please enter a date at least an hour out.",
            )
