"""
Constantes globales para la aplicación
"""

class Constants:
    """Constantes de configuración del sistema"""
    
    # Rango de rating de usuarios
    MIN_USER_RATING = 1000
    MAX_USER_RATING = 3000
    DEFAULT_USER_RATING = 1500
    
    # Rango de tier de problemas (solved.ac)
    MIN_PROBLEM_TIER = 0
    MAX_PROBLEM_TIER = 30
    
    @staticmethod
    def tier_to_rating(tier):
        """
        Convierte un tier de problema (0-30) a rating equivalente (1000-3000)
        Mapeo lineal: tier 0 = 1000, tier 15 = 2000, tier 30 = 3000
        
        Args:
            tier: Tier del problema (0-30)
            
        Returns:
            Rating equivalente (1000-3000)
        """
        if tier is None:
            return Constants.DEFAULT_USER_RATING
        
        # Asegurar que tier es un número (puede venir como string de la BD)
        try:
            tier = float(tier)
        except (ValueError, TypeError):
            return Constants.DEFAULT_USER_RATING
        
        # Limitar tier al rango válido
        tier = max(Constants.MIN_PROBLEM_TIER, min(Constants.MAX_PROBLEM_TIER, tier))
        
        # Conversión lineal: rating = 1000 + (tier / 30) * 2000
        rating_range = Constants.MAX_USER_RATING - Constants.MIN_USER_RATING
        rating = Constants.MIN_USER_RATING + (tier / Constants.MAX_PROBLEM_TIER) * rating_range
        
        return int(rating)
    
    @staticmethod
    def rating_to_tier(rating):
        """
        Convierte un rating de usuario (1000-3000) a tier equivalente (0-30)
        Mapeo lineal: rating 1000 = tier 0, rating 2000 = tier 15, rating 3000 = tier 30
        
        Args:
            rating: Rating del usuario (1000-3000)
            
        Returns:
            Tier equivalente (0-30)
        """
        if rating is None:
            rating = Constants.DEFAULT_USER_RATING
        
        # Asegurar que rating es un número (puede venir como string de la BD)
        try:
            rating = float(rating)
        except (ValueError, TypeError):
            rating = Constants.DEFAULT_USER_RATING
        
        # Limitar rating al rango válido
        rating = max(Constants.MIN_USER_RATING, min(Constants.MAX_USER_RATING, rating))
        
        # Conversión lineal: tier = (rating - 1000) * 30 / 2000
        rating_range = Constants.MAX_USER_RATING - Constants.MIN_USER_RATING
        tier = (rating - Constants.MIN_USER_RATING) * Constants.MAX_PROBLEM_TIER / rating_range
        
        return int(tier)

