from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Time, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# --- Definición de Modelos (ORM) ---
# Estas clases representan nuestras tablas de base de datos.
# Cada clase hereda de 'Base', vinculándola a la configuración de SQLAlchemy.

class User(Base):
    """
    Representa a un usuario registrado en el sistema.
    Almacena información básica y credenciales (hash de contraseña).
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)        # Nombre del usuario
    surname = Column(String, nullable=False)     # Apellidos
    email = Column(String, unique=True, index=True, nullable=False) # Email único (usado para login)
    password_hash = Column(String, nullable=False) # Hash seguro de la contraseña

    # Relaciones
    # Relación One-to-One con Permissions (un usuario tiene un set de permisos)
    permissions = relationship("Permission", back_populates="user", uselist=False, cascade="all, delete-orphan")
    # Relación One-to-Many con Bookings (un usuario puede tener muchas reservas)
    bookings = relationship("Booking", back_populates="user")

class Permission(Base):
    """
    Almacena los permisos específicos de cada usuario.
    Controla quién puede alquilar, editar horarios o cambiar precios.
    """
    __tablename__ = "permissions"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    
    is_admin = Column(Boolean, default=False)          # ¿Es administrador global?
    can_rent = Column(Boolean, default=True)           # ¿Puede realizar alquileres? (Por defecto SI)
    can_edit_schedule = Column(Boolean, default=False) # ¿Puede modificar el cuadrante horario?
    can_edit_price = Column(Boolean, default=False)    # ¿Puede modificar las tarifas?

    # Relación inversa hacia el Usuario
    user = relationship("User", back_populates="permissions")

class Court(Base):
    """
    Representa una pista deportiva (tenis/pádel).
    Existen 8 pistas fijas, numeradas del 1 al 8.
    """
    __tablename__ = "courts"

    court_id = Column(Integer, primary_key=True, index=True) # ID identificador (1-8)
    is_covered = Column(Boolean, default=False)             # ¿Es pista cubierta?

    # Relación con las reservas de esta pista
    bookings = relationship("Booking", back_populates="court")

class Demand(Base):
    """
    Define los niveles de demanda (Ej: Alta, Media, Baja).
    Sirve como puente para asignar precios dinámicos según el horario.
    """
    __tablename__ = "demands"

    demand_id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=True) # Descripción del nivel de demanda
    is_active = Column(Boolean, default=True)   # Estado del nivel

class Price(Base):
    """
    Registro histórico de precios asociados a un nivel de demanda.
    Permite mantener un histórico de cuánto costaba una pista en una fecha determinada.
    """
    __tablename__ = "prices"

    price_id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)           # Importe de la tarifa
    start_date = Column(DateTime, default=datetime.utcnow) # Fecha de entrada en vigor
    end_date = Column(DateTime, nullable=True)       # Fecha de fin (nulo si es la vigente)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)        # ¿Es la tarifa actual activa?
    demand_id = Column(Integer, ForeignKey("demands.demand_id"), nullable=False)

    # Relaciones
    bookings = relationship("Booking", back_populates="price_snapshot")
    demand = relationship("Demand")

class Schedule(Base):
    """
    Define los slots de disponibilidad semanal (cuadrante horario).
    Relaciona un día y hora específicos con un nivel de demanda.
    """
    __tablename__ = "schedules"

    schedule_id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(Integer, nullable=False) # 0=Lunes, 6=Domingo
    is_weekend = Column(Boolean, default=False)   # Flag para fin de semana
    start_time = Column(Time, nullable=False)     # Hora de inicio del bloque (ej, 08:30)
    demand_id = Column(Integer, ForeignKey("demands.demand_id"), nullable=False)
    
    # Relación con el nivel de demanda asociado al horario
    demand = relationship("Demand")

class Holiday(Base):
    """
    Almacena fechas especiales (festivos) donde el horario podría variar.
    """
    __tablename__ = "holidays"

    date = Column(DateTime, primary_key=True)

class Booking(Base):
    """
    Representa una reserva realizada por un usuario.
    Guarda una captura (snapshot) del precio en el momento exacto del alquiler.
    """
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    court_id = Column(Integer, ForeignKey("courts.court_id"))
    
    # Vinculamos al price_id específico en el MOMENTO de la reserva para preservar el histórico
    price_id = Column(Integer, ForeignKey("prices.price_id")) 
    
    start_time = Column(DateTime, nullable=False)      # Fecha y hora exacta del alquiler
    created_at = Column(DateTime, default=datetime.utcnow) # Cuándo se realizó la reserva
    is_cancelled = Column(Boolean, default=False)      # Flag de cancelación
    
    # Relaciones para navegar entre modelos
    user = relationship("User", back_populates="bookings")
    court = relationship("Court", back_populates="bookings")
    price_snapshot = relationship("Price", back_populates="bookings")
