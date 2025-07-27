# tests/test_performance.py
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
from app import create_app, db
from app.services.guest_service import GuestService
from app.services.rsvp_service import RSVPService
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.constants import GuestLimit

class PerformanceBenchmark:
    """Base class for performance benchmarks."""
    
    def measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        return result, end - start
    
    def run_benchmark(self, func, iterations=10, *args, **kwargs):
        """Run a benchmark multiple times and return statistics."""
        times = []
        for _ in range(iterations):
            _, duration = self.measure_time(func, *args, **kwargs)
            times.append(duration)
        
        return {
            'min': min(times),
            'max': max(times),
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0
        }


class TestGuestServicePerformance(PerformanceBenchmark):
    """Performance tests for GuestService."""
    
    @pytest.fixture
    def app(self):
        """Create app with test config."""
        from app.config import TestConfig
        app = create_app(TestConfig)
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_guest_creation_performance(self, app):
        """Test performance of creating guests."""
        with app.app_context():
            def create_guest():
                return GuestService.create_guest(
                    name=f"Perf Test {time.time()}",
                    phone=f"555-{int(time.time() * 1000) % 10000:04d}"
                )
            
            stats = self.run_benchmark(create_guest, iterations=50)
            
            # Assert performance requirements
            assert stats['mean'] < 0.1, f"Guest creation too slow: {stats['mean']:.3f}s average"
            assert stats['max'] < 0.2, f"Guest creation max time too high: {stats['max']:.3f}s"
            
            print(f"\nGuest Creation Performance:")
            print(f"  Mean: {stats['mean']*1000:.2f}ms")
            print(f"  Min: {stats['min']*1000:.2f}ms")
            print(f"  Max: {stats['max']*1000:.2f}ms")
    
    def test_guest_lookup_performance(self, app):
        """Test performance of guest lookups."""
        with app.app_context():
            # Create test guests
            guests = []
            for i in range(100):
                guest = GuestService.create_guest(
                    name=f"Lookup Test {i}",
                    phone=f"555-{1000+i:04d}",
                    email=f"lookup{i}@test.com"
                )
                guests.append(guest)
            
            # Test token lookup
            def lookup_by_token():
                guest = guests[50]  # Middle guest
                return GuestService.get_guest_by_token(guest.token)
            
            token_stats = self.run_benchmark(lookup_by_token, iterations=100)
            
            # Test email lookup
            def lookup_by_email():
                return GuestService.find_guest_by_email_or_phone(email="lookup50@test.com")
            
            email_stats = self.run_benchmark(lookup_by_email, iterations=100)
            
            # Assert performance requirements
            assert token_stats['mean'] < 0.01, f"Token lookup too slow: {token_stats['mean']:.3f}s"
            assert email_stats['mean'] < 0.01, f"Email lookup too slow: {email_stats['mean']:.3f}s"
            
            print(f"\nGuest Lookup Performance:")
            print(f"  Token lookup mean: {token_stats['mean']*1000:.2f}ms")
            print(f"  Email lookup mean: {email_stats['mean']*1000:.2f}ms")
    
    def test_statistics_calculation_performance(self, app):
        """Test performance of statistics calculation with many guests."""
        with app.app_context():
            # Create many guests and RSVPs
            print("\nCreating test data...")
            for i in range(200):
                guest = GuestService.create_guest(
                    name=f"Stats Test {i}",
                    phone=f"555-{2000+i:04d}"
                )
                if i % 3 == 0:  # 1/3 attending
                    rsvp = RSVP(guest_id=guest.id, is_attending=True)
                    db.session.add(rsvp)
                elif i % 3 == 1:  # 1/3 declined
                    rsvp = RSVP(guest_id=guest.id, is_attending=False)
                    db.session.add(rsvp)
                # 1/3 no response
            db.session.commit()
            
            def calculate_stats():
                return GuestService.get_guest_statistics()
            
            stats = self.run_benchmark(calculate_stats, iterations=20)
            
            # Assert performance requirements
            assert stats['mean'] < 0.1, f"Statistics calculation too slow: {stats['mean']:.3f}s"
            
            print(f"\nStatistics Calculation Performance (200 guests):")
            print(f"  Mean: {stats['mean']*1000:.2f}ms")
            print(f"  Max: {stats['max']*1000:.2f}ms")


class TestRSVPServicePerformance(PerformanceBenchmark):
    """Performance tests for RSVPService."""
    
    @pytest.fixture
    def app_with_data(self):
        """Create app with test data."""
        from app.config import TestConfig
        app = create_app(TestConfig)
        with app.app_context():
            db.create_all()
            
            # Create allergens
            from app.models.allergen import Allergen
            for name in ['Nuts', 'Dairy', 'Gluten']:
                allergen = Allergen(name=name)
                db.session.add(allergen)
            db.session.commit()
            
            yield app
            
            db.session.remove()
            db.drop_all()
    
    def test_rsvp_submission_performance(self, app_with_data):
        """Test performance of RSVP submission."""
        with app_with_data.app_context():
            # Create test guest
            guest = GuestService.create_guest(
                name="RSVP Perf Test",
                phone="555-9999",
                is_family=True
            )
            
            def submit_rsvp():
                form_data = {
                    'is_attending': 'yes',
                    'hotel_name': 'Test Hotel',
                    'adults_count': '2',
                    'children_count': '1',
                    'adult_name_0': 'Adult One',
                    'adult_name_1': 'Adult Two',
                    'child_name_0': 'Child One',
                    'allergens_main': ['1', '2'],
                    'custom_allergen_main': 'Shellfish'
                }
                return RSVPService.create_or_update_rsvp(guest, form_data)
            
            stats = self.run_benchmark(submit_rsvp, iterations=20)
            
            # Assert performance requirements
            assert stats['mean'] < 0.2, f"RSVP submission too slow: {stats['mean']:.3f}s"
            
            print(f"\nRSVP Submission Performance:")
            print(f"  Mean: {stats['mean']*1000:.2f}ms")
            print(f"  Max: {stats['max']*1000:.2f}ms")
    
    def test_concurrent_rsvp_submissions(self, app_with_data):
        """Test concurrent RSVP submissions."""
        with app_with_data.app_context():
            # Create multiple guests
            guests = []
            for i in range(10):
                guest = GuestService.create_guest(
                    name=f"Concurrent Test {i}",
                    phone=f"555-{3000+i:04d}"
                )
                guests.append(guest)
            
            def submit_rsvp_for_guest(guest):
                """Submit RSVP in app context."""
                with app_with_data.app_context():
                    form_data = {
                        'is_attending': 'yes',
                        'hotel_name': f'Hotel {guest.id}'
                    }
                    return RSVPService.create_or_update_rsvp(guest, form_data)
            
            # Submit RSVPs concurrently
            start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(submit_rsvp_for_guest, guest) for guest in guests]
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        pytest.fail(f"Concurrent submission failed: {e}")
            
            end = time.perf_counter()
            duration = end - start
            
            # Verify all submissions succeeded
            assert len(results) == 10, "Not all concurrent submissions completed"
            assert all(r[0] for r in results), "Some submissions failed"
            
            print(f"\nConcurrent RSVP Submission Performance (10 guests, 5 workers):")
            print(f"  Total time: {duration:.2f}s")
            print(f"  Average per submission: {duration/10*1000:.2f}ms")