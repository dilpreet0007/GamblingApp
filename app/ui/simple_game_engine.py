from app.ui.game_status_display import GameStatusDisplay
from app.ui.interactive_menu import InteractiveMenu
from app.ui.session_summary import SessionSummary

from app.services.win_loss_calculator import WinLossCalculator
from app.services.game_session_manager import GameSessionManager
from app.models.odds_config import OddsConfig, OddsType
from app.models.session_parameters import SessionParameters
from app.models.game_record import GameRecord
from app.validation.input_validator import InputValidator
from app.validation.validation_config import ValidationConfig


class SimpleGameEngine:

    def __init__(self, gambler_id, stake_service, gambler_service, initial_stake, win_threshold, loss_threshold):

        self.gambler_id = gambler_id
        self.stake_service = stake_service
        self.gambler_service = gambler_service
        self.initial_stake = initial_stake
        self.win_threshold = win_threshold
        self.loss_threshold = loss_threshold

        self.display = GameStatusDisplay()
        self.menu = InteractiveMenu()
        self.summary = SessionSummary()

        self.calculator = WinLossCalculator()
        self.validator = InputValidator(ValidationConfig())
        self.session_manager = GameSessionManager()

        self.odds = OddsConfig(OddsType.FIXED, 2)
        self.current_session = None

    def run(self):
        # Initialize gaming session
        params = SessionParameters(
            min_stake=self.loss_threshold,
            max_stake=self.win_threshold,
            min_bet=10,
            max_bet=1000,
            max_games=100,
            max_duration=3600,
            probability=0.5
        )
        self.current_session = self.session_manager.start_new_session(
            self.gambler_id,
            params,
            self.initial_stake
        )
        print(f"\n=== Gaming Session Started ===")
        print(f"Session ID: {id(self.current_session)}")

        while True:

            self.menu.display_main_menu()
            choice = self.menu.get_choice()

            if choice == 1:
                self.display.display_current_status(
                    self.gambler_id,
                    self.stake_service
                )

            elif choice == 2:
                self.handle_single_bet()

            elif choice == 3:
                self.handle_multiple_bets()

            elif choice == 4:
                self.summary.display_session_summary(self.calculator)

            elif choice == 5:
                self.pause_session()

            elif choice == 6:
                self.resume_session()

            elif choice == 7:
                print("Exiting...")
                self._end_session()
                break

            else:
                print("Invalid choice")

    def handle_single_bet(self):

        if self.current_session.status.value != "ACTIVE":
            print("\n✗ Cannot place bet: Session is not active (paused or ended)")
            return

        bet = self.menu.prompt_bet_amount()

        if bet is None:
            print("Invalid input")
            return

        stake = self.stake_service.get_current_stake(self.gambler_id)

        validation = self.validator.validate_bet_amount(bet, stake)

        if not validation.is_valid():
            print(validation.summary())
            return

        result = self.calculator.play(
            bet,
            stake,
            0.5,
            self.odds
        )

        self.stake_service.update_stake(self.gambler_id, result.stake_after)

        self.stake_service.insert_bet(self.gambler_id, bet, 0.5, result.outcome, stake, result.stake_after)

        self.display.display_game_outcome(result)

        # Record game in session
        game_record = GameRecord(bet, result.outcome, stake, result.stake_after)
        self.current_session.games.append(game_record)

        # Update current session stake
        self.current_session.current_stake = result.stake_after

        # Check thresholds
        if result.stake_after >= self.win_threshold:
            print(f"\nCongratulations! You reached the win threshold of {self.win_threshold}. Session ended!")
            self._end_session()
            exit()
        elif result.stake_after <= self.loss_threshold:
            print(f"\nSorry! You reached the loss threshold of {self.loss_threshold}. Session ended!")
            self._end_session()
            exit()

    def handle_multiple_bets(self):

        for _ in range(5):
            if self.current_session.status.value != "ACTIVE":
                break
            self.handle_single_bet()

    def _end_session(self):
        if self.current_session:
            session_summary = self.current_session.summary()
            print("\n=== Gaming Session Summary ===")
            print(f"Status: {session_summary['status']}")
            print(f"Games Played: {session_summary['games_played']}")
            print(f"Wins: {session_summary['wins']}")
            print(f"Losses: {session_summary['losses']}")
            print(f"Final Stake: {self.current_session.current_stake}")
            self.session_manager._end_session(self.gambler_id)

    def pause_session(self):
        if self.current_session:
            if self.current_session.status.value == "ACTIVE":
                self.current_session.pause()
                print("\n✓ Session Paused")
                print(f"Current Stake: {self.current_session.current_stake}")
            else:
                print("\n✗ Cannot pause: Session is not active")

    def resume_session(self):
        if self.current_session:
            if self.current_session.status.value == "PAUSED":
                self.current_session.resume()
                print("\n✓ Session Resumed")
                print(f"Current Stake: {self.current_session.current_stake}")
            else:
                print("\n✗ Cannot resume: Session is not paused")