import math

class RatingCalculator:
    """
    Calculadora de rating basada en una adaptación del sistema Elo
    para problemas de programación.
    """
    
    # Factor K que determina el cambio máximo posible
    K_FACTOR = 32
    
    @staticmethod
    def calculate_rating_change(user_rating, problem_level):
        """
        Calcula el cambio de rating cuando un usuario resuelve un problema
        
        Args:
            user_rating: Rating actual del usuario
            problem_level: Nivel del problema resuelto
            
        Returns:
            Cambio en el rating (positivo)
        """
        # Si el problema no tiene nivel definido, usar un valor predeterminado
        if problem_level is None:
            problem_level = 1500
        
        # Calcular la expectativa (probabilidad esperada de resolver el problema)
        expectation = 1 / (1 + math.pow(10, (problem_level - user_rating) / 400))
        
        # Calcular el cambio de rating (redondeado a entero)
        delta_rating = round(RatingCalculator.K_FACTOR * (1 - expectation))
        
        return delta_rating
    
    @staticmethod
    def calculate_rating_loss(user_rating, problem_level):
        """
        Calcula la pérdida de rating cuando un usuario no puede resolver un problema
        
        Args:
            user_rating: Rating actual del usuario
            problem_level: Nivel del problema no resuelto
            
        Returns:
            Cambio en el rating (negativo)
        """
        # Si el problema no tiene nivel definido, usar un valor predeterminado
        if problem_level is None:
            problem_level = 1500
        
        # Calcular la expectativa (probabilidad esperada de resolver el problema)
        expectation = 1 / (1 + math.pow(10, (problem_level - user_rating) / 400))
        
        # Calcular el cambio de rating (redondeado a entero y negativo)
        delta_rating = round(RatingCalculator.K_FACTOR * (0 - expectation))
        
        return delta_rating 