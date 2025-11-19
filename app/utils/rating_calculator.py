import math
from app.utils.constants import Constants

class RatingCalculator:
    """
    Calculadora de rating basada en una adaptación del sistema Elo
    para problemas de programación.
    """
    
    # Factor K que determina el cambio máximo posible (configurado dinámicamente)
    @staticmethod
    def get_k_factor():
        """Retorna el factor K para el cálculo de rating"""
        return 32
    
    @staticmethod
    def calculate_rating_change(user_rating, problem_tier):
        """
        Calcula el cambio de rating cuando un usuario resuelve un problema
        
        Args:
            user_rating: Rating actual del usuario
            problem_tier: Tier del problema resuelto (0-30)
            
        Returns:
            Cambio en el rating (positivo)
        """
        # Convertir tier a rating equivalente para la fórmula Elo
        problem_rating = Constants.tier_to_rating(problem_tier)
        
        # Calcular la expectativa (probabilidad esperada de resolver el problema)
        expectation = 1 / (1 + math.pow(10, (problem_rating - user_rating) / 400))
        
        # Calcular el cambio de rating (redondeado a entero)
        k_factor = RatingCalculator.get_k_factor()
        delta_rating = round(k_factor * (1 - expectation))
        
        return delta_rating
    
    @staticmethod
    def calculate_rating_loss(user_rating, problem_tier):
        """
        Calcula la pérdida de rating cuando un usuario no puede resolver un problema
        
        Args:
            user_rating: Rating actual del usuario
            problem_tier: Tier del problema no resuelto (0-30)
            
        Returns:
            Cambio en el rating (negativo)
        """
        # Convertir tier a rating equivalente para la fórmula Elo
        problem_rating = Constants.tier_to_rating(problem_tier)
        
        # Calcular la expectativa (probabilidad esperada de resolver el problema)
        expectation = 1 / (1 + math.pow(10, (problem_rating - user_rating) / 400))
        
        # Calcular el cambio de rating (redondeado a entero y negativo)
        k_factor = RatingCalculator.get_k_factor()
        delta_rating = round(k_factor * (0 - expectation))
        
        return delta_rating 