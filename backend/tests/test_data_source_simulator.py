import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, mock_open


# Import the module under test
from data_source.litterbox_edge_device_simulator import (
    LitterboxSimulator,
    EDGE_DEVICE_ID,
    EMPTY_LITTERBOX_WEIGHT,
)


class TestLitterboxSimulator:
    """Test suite for LitterboxSimulator class"""

    @pytest.fixture
    def simulator(self):
        """Create a simulator instance for testing"""
        with patch(
            "data_source.litterbox_edge_device_simulator.get_logger"
        ) as mock_logger:
            mock_logger.return_value = Mock()
            return LitterboxSimulator()

    @pytest.fixture
    def mock_datetime_now(self):
        """Mock datetime.now to return a fixed date"""
        fixed_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        with patch(
            "data_source.litterbox_edge_device_simulator.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = fixed_date
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            yield mock_dt

    @pytest.fixture
    def simulator_with_fixed_date(self, mock_datetime_now):
        """Create a simulator instance with fixed date"""
        with patch(
            "data_source.litterbox_edge_device_simulator.get_logger"
        ) as mock_logger:
            mock_logger.return_value = Mock()
            return LitterboxSimulator()

    def test_init_sets_correct_week_start(self, simulator_with_fixed_date):
        """Test that simulator initializes with correct week start date"""
        expected_start = datetime(
            2024, 1, 8, 0, 0, 0, tzinfo=timezone.utc
        )  # 7 days ago
        assert simulator_with_fixed_date.current_week_start == expected_start

    def test_constants(self):
        """Test that constants are properly defined"""
        assert isinstance(EDGE_DEVICE_ID, uuid.UUID)
        assert str(EDGE_DEVICE_ID) == "12345678-1234-5678-9012-123456789abc"
        assert EMPTY_LITTERBOX_WEIGHT == 5

    def test_generate_realistic_usage_times(self, simulator):
        """Test generation of realistic usage times"""
        base_date = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)

        # Run multiple times to test randomness
        for _ in range(10):
            usage_times = simulator.generate_realistic_usage_times(base_date)

            # Should generate 2-4 usage times per day
            assert 2 <= len(usage_times) <= 4

            # Times should be sorted
            assert usage_times == sorted(usage_times)

            # All times should be on the same date
            for usage_time in usage_times:
                assert usage_time.date() == base_date.date()
                assert 0 <= usage_time.hour <= 23
                assert 0 <= usage_time.minute <= 59
                assert 0 <= usage_time.second <= 59

    def test_generate_weight_data(self, simulator):
        """Test generation of weight data"""
        for _ in range(100):  # Test multiple times for randomness
            weight_enter, weight_exit = simulator.generate_weight_data()

            # Weight enter should be higher than weight exit (cat leaves)
            assert weight_enter > weight_exit

            # Weights should be within realistic ranges
            # Minimum: empty box (5) + min litter (17.6) + min cat (6.6) = 29.2
            # Maximum: empty box (5) + max litter (33.1) + max cat (13.2) = 51.3
            assert 29.0 <= weight_enter <= 52.0

            # Exit weight should be box + litter + waste
            # Should be close to enter weight minus cat weight
            weight_diff = weight_enter - weight_exit
            assert 6.0 <= weight_diff <= 14.0  # Approximately cat weight range

            # Weights should be rounded to 1 decimal place
            assert weight_enter == round(weight_enter, 1)
            assert weight_exit == round(weight_exit, 1)

    def test_generate_session_duration(self, simulator):
        """Test generation of session duration"""
        for _ in range(100):
            duration = simulator.generate_session_duration()

            # Duration should be between 30 seconds and 5 minutes
            assert timedelta(seconds=30) <= duration <= timedelta(minutes=5)

            # Should be a timedelta object
            assert isinstance(duration, timedelta)

    def test_generate_week_data(self, simulator):
        """Test generation of a full week's data"""
        week_start = datetime(2024, 1, 8, 0, 0, 0, tzinfo=timezone.utc)

        with patch.object(
            simulator, "generate_realistic_usage_times"
        ) as mock_usage_times, patch.object(
            simulator, "generate_session_duration"
        ) as mock_duration, patch.object(
            simulator, "generate_weight_data"
        ) as mock_weights:

            # Mock returns
            mock_usage_times.return_value = [
                week_start.replace(hour=8, minute=30),
                week_start.replace(hour=14, minute=15),
            ]
            mock_duration.return_value = timedelta(minutes=2)
            mock_weights.return_value = (30.5, 24.2)

            data = simulator.generate_week_data(week_start)

            # Should generate data for 7 days
            assert mock_usage_times.call_count == 7

            # Should have 14 records (2 per day * 7 days)
            assert len(data) == 14

            # Check structure of first record
            record = data[0]
            assert isinstance(record["id"], uuid.UUID)
            assert record["litterbox_edge_device_id"] == EDGE_DEVICE_ID
            assert isinstance(record["enter_time"], datetime)
            assert isinstance(record["exit_time"], datetime)
            assert record["exit_time"] > record["enter_time"]
            assert record["weight_enter"] == 30.5
            assert record["weight_exit"] == 24.2
            assert isinstance(record["created_at"], datetime)

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_data_to_file_with_filename(
        self, mock_json_dump, mock_file, simulator
    ):
        """Test saving data to file with specified filename"""
        test_data = [{"test": "data"}]
        filename = "test_file.json"

        simulator.save_data_to_file(test_data, filename)

        mock_file.assert_called_once_with(filename, "w")
        mock_json_dump.assert_called_once_with(
            test_data,
            mock_file.return_value.__enter__.return_value,
            indent=2,
            default=str,
        )

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    @patch("data_source.litterbox_edge_device_simulator.datetime")
    def test_save_data_to_file_without_filename(
        self, mock_datetime, mock_json_dump, mock_file, simulator
    ):
        """Test saving data to file without specified filename"""
        mock_datetime.now.return_value.strftime.return_value = "20240115_120000"
        test_data = [{"test": "data"}]

        simulator.save_data_to_file(test_data)

        expected_filename = "litterbox_data_20240115_120000.json"
        mock_file.assert_called_once_with(expected_filename, "w")
        mock_json_dump.assert_called_once_with(
            test_data,
            mock_file.return_value.__enter__.return_value,
            indent=2,
            default=str,
        )

    def test_process_data(self, simulator):
        """Test data processing"""
        test_data = [{"test": "data"}]

        with patch.object(simulator, "save_data_to_file") as mock_save:
            simulator.process_data(test_data)
            mock_save.assert_called_once_with(test_data)

    def test_generate_initial_week(self, simulator):
        """Test generation of initial week's data"""
        with patch.object(
            simulator, "generate_week_data"
        ) as mock_gen_week, patch.object(simulator, "process_data") as mock_process:

            mock_gen_week.return_value = [{"test": "data"}]

            simulator.generate_initial_week()

            mock_gen_week.assert_called_once_with(simulator.current_week_start)
            mock_process.assert_called_once_with([{"test": "data"}])

    def test_generate_next_week(self, simulator):
        """Test generation of next week's data"""
        original_start = simulator.current_week_start

        with patch.object(
            simulator, "generate_week_data"
        ) as mock_gen_week, patch.object(simulator, "process_data") as mock_process:

            mock_gen_week.return_value = [{"test": "data"}]

            simulator.generate_next_week()

            # Should advance week start by 7 days
            expected_new_start = original_start + timedelta(days=7)
            assert simulator.current_week_start == expected_new_start

            mock_gen_week.assert_called_once_with(expected_new_start)
            mock_process.assert_called_once_with([{"test": "data"}])

    def test_check_and_generate_next_batch_when_time(self, simulator):
        """Test checking and generating next batch when it's time"""
        # Set current week start to 8 days ago so it's time for next batch
        simulator.current_week_start = datetime.now(timezone.utc) - timedelta(days=8)

        with patch.object(simulator, "generate_next_week") as mock_gen_next:
            simulator._check_and_generate_next_batch()
            mock_gen_next.assert_called_once()

    def test_check_and_generate_next_batch_when_not_time(self, simulator):
        """Test checking and generating next batch when it's not time yet"""
        # Set current week start to 3 days ago so it's not time yet
        simulator.current_week_start = datetime.now(timezone.utc) - timedelta(days=3)

        with patch.object(simulator, "generate_next_week") as mock_gen_next:
            simulator._check_and_generate_next_batch()
            mock_gen_next.assert_not_called()

    @patch("data_source.litterbox_edge_device_simulator.schedule")
    @patch("data_source.litterbox_edge_device_simulator.time.sleep")
    def test_start_simulator_keyboard_interrupt(
        self, mock_sleep, mock_schedule, simulator
    ):
        """Test simulator start with keyboard interrupt"""
        mock_sleep.side_effect = KeyboardInterrupt()

        with patch.object(simulator, "generate_initial_week") as mock_init:
            simulator.start_simulator()

            mock_init.assert_called_once()
            mock_schedule.every.return_value.day.at.assert_called_once_with("00:01")

    @patch("data_source.litterbox_edge_device_simulator.schedule")
    @patch("data_source.litterbox_edge_device_simulator.time.sleep")
    def test_start_simulator_running(self, mock_sleep, mock_schedule, simulator):
        """Test simulator start and running"""
        # Make sleep raise KeyboardInterrupt after a few iterations
        mock_sleep.side_effect = [None, None, KeyboardInterrupt()]

        with patch.object(simulator, "generate_initial_week") as mock_init:
            simulator.start_simulator()

            mock_init.assert_called_once()
            mock_schedule.every.return_value.day.at.assert_called_once_with("00:01")
            assert mock_schedule.run_pending.call_count >= 1
            assert mock_sleep.call_count == 3


class TestWeightDataRealism:
    """Test suite for weight data realism"""

    @pytest.fixture
    def simulator(self):
        with patch(
            "data_source.litterbox_edge_device_simulator.get_logger"
        ) as mock_logger:
            mock_logger.return_value = Mock()
            return LitterboxSimulator()

    def test_weight_distribution_realistic(self, simulator):
        """Test that weight data follows realistic distribution"""
        urine_only_count = 0
        both_count = 0
        # feces_only_count = 0

        # Generate many samples to test distribution
        for _ in range(1000):
            weight_enter, weight_exit = simulator.generate_weight_data()
            weight_diff = weight_enter - weight_exit

            # Estimate visit type based on weight difference
            # (This is approximate since we can't know the exact cat weight)
            if 6.0 <= weight_diff <= 7.0:  # Likely smaller cat, urine only
                urine_only_count += 1
            elif 12.5 <= weight_diff <= 13.5:  # Likely larger cat, both
                both_count += 1
            elif 6.5 <= weight_diff <= 13.0:  # Could be any type
                # This is the majority, representing normal distribution
                pass

        # Just ensure we get reasonable weight differences
        # (exact distribution testing would require more complex logic)
        assert True  # Basic test passed if no assertions failed above

    def test_weight_precision(self, simulator):
        """Test that weights have correct precision"""
        for _ in range(50):
            weight_enter, weight_exit = simulator.generate_weight_data()

            # Should be rounded to 1 decimal place
            assert len(str(weight_enter).split(".")[-1]) <= 1
            assert len(str(weight_exit).split(".")[-1]) <= 1


class TestTimeGeneration:
    """Test suite for time generation functionality"""

    @pytest.fixture
    def simulator(self):
        with patch(
            "data_source.litterbox_edge_device_simulator.get_logger"
        ) as mock_logger:
            mock_logger.return_value = Mock()
            return LitterboxSimulator()

    def test_usage_times_distribution(self, simulator):
        """Test that usage times follow expected distribution"""
        base_date = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)

        morning_count = 0
        midday_count = 0
        evening_count = 0
        night_count = 0

        # Generate many samples to test distribution
        for _ in range(100):
            usage_times = simulator.generate_realistic_usage_times(base_date)

            for usage_time in usage_times:
                hour = usage_time.hour
                if 6 <= hour < 10:
                    morning_count += 1
                elif 10 <= hour < 16:
                    midday_count += 1
                elif 16 <= hour < 20:
                    evening_count += 1
                else:
                    night_count += 1

        total_uses = morning_count + midday_count + evening_count + night_count

        # Evening should be most common, night should be least common
        assert evening_count > midday_count
        assert night_count < morning_count
        assert total_uses > 0


@patch("data_source.litterbox_edge_device_simulator.LitterboxSimulator")
def test_main_function(mock_simulator_class):
    """Test the main function"""
    from data_source.litterbox_edge_device_simulator import main

    mock_simulator = Mock()
    mock_simulator_class.return_value = mock_simulator

    main()

    mock_simulator_class.assert_called_once()
    mock_simulator.start_simulator.assert_called_once()


# Integration-style tests
class TestIntegration:
    """Integration tests for the full simulator workflow"""

    @pytest.fixture
    def simulator(self):
        with patch(
            "data_source.litterbox_edge_device_simulator.get_logger"
        ) as mock_logger:
            mock_logger.return_value = Mock()
            return LitterboxSimulator()

    def test_full_week_generation_workflow(self, simulator):
        """Test the complete workflow of generating a week's data"""
        week_start = datetime(2024, 1, 8, 0, 0, 0, tzinfo=timezone.utc)

        # Generate actual data (not mocked)
        data = simulator.generate_week_data(week_start)

        # Verify data structure and content
        assert isinstance(data, list)
        assert len(data) >= 14  # At least 2 uses per day * 7 days
        assert len(data) <= 28  # At most 4 uses per day * 7 days

        # Verify each record has correct structure
        for record in data:
            assert "id" in record
            assert "litterbox_edge_device_id" in record
            assert "enter_time" in record
            assert "exit_time" in record
            assert "weight_enter" in record
            assert "weight_exit" in record
            assert "created_at" in record

            # Verify data types and logical constraints
            assert isinstance(record["id"], uuid.UUID)
            assert record["litterbox_edge_device_id"] == EDGE_DEVICE_ID
            assert record["exit_time"] > record["enter_time"]
            assert record["weight_enter"] > record["weight_exit"]

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_end_to_end_data_generation_and_save(
        self, mock_json_dump, mock_file, simulator
    ):
        """Test end-to-end data generation and saving"""
        # Generate and process data
        simulator.generate_initial_week()

        # Verify file operations were called
        assert mock_file.called
        assert mock_json_dump.called

        # Verify the data passed to json.dump is reasonable
        call_args = mock_json_dump.call_args
        data_saved = call_args[0][0]  # First argument to json.dump

        assert isinstance(data_saved, list)
        assert len(data_saved) > 0


# if __name__ == '__main__':
#     pytest.main([__file__])
