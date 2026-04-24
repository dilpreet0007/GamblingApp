from app.services.gambler_service import GamblerProfileService
from app.services.stake_management_service import StakeManagementService

from app.validation.input_validator import InputValidator
from app.validation.validation_config import ValidationConfig

from app.ui.simple_game_engine import SimpleGameEngine


if __name__ == "__main__":

    gambler_service = GamblerProfileService()
    stake_service = StakeManagementService()
    validator = InputValidator(ValidationConfig())

    print("Enter Gambler Details")
    name = input("Name: ")
    email = input("Email: ")

    initial_stake = float(input("Initial Stake: "))
    upper_limit = float(input("Upper Limit: "))
    lower_limit = float(input("Lower Limit: "))

    stake_validation = validator.validate_initial_stake(initial_stake)
    limit_validation = validator.validate_limits(
        lower_limit,
        upper_limit,
        initial_stake
    )

    if not (stake_validation.is_valid() and limit_validation.is_valid()):
        print("Validation Failed")
        print(stake_validation.summary())
        print(limit_validation.summary())
        exit()

    gambler_id = gambler_service.create_gambler(
        name,
        email,
        initial_stake,
        upper_limit,
        lower_limit
    )

    stake_service.initialize_stake(gambler_id, initial_stake)

    engine = SimpleGameEngine(gambler_id, stake_service, gambler_service, initial_stake, upper_limit, lower_limit)
    engine.run()

    print(gambler_service.get_statistics(gambler_id))
    print(gambler_service.validate_gambler(gambler_id))