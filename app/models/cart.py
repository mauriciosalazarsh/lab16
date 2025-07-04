from dataclasses import dataclass
from typing import List, Dict

@dataclass
class CartItem:
    product_id: int
    name: str
    price: float
    quantity: int
    
    def to_dict(self) -> Dict:
        return {
            'product_id': self.product_id,
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity
        }

@dataclass
class Cart:
    user_id: str
    items: List[CartItem]
    
    @property
    def total(self) -> float:
        return sum(item.price * item.quantity for item in self.items)
    
    def add_item(self, item: CartItem) -> None:
        # Buscar si el producto ya existe
        for existing_item in self.items:
            if existing_item.product_id == item.product_id:
                existing_item.quantity += item.quantity
                return
        self.items.append(item)
    
    def remove_item(self, product_id: int) -> bool:
        initial_length = len(self.items)
        self.items = [item for item in self.items if item.product_id != product_id]
        return len(self.items) < initial_length
    
    def update_quantity(self, product_id: int, quantity: int) -> bool:
        for item in self.items:
            if item.product_id == product_id:
                item.quantity = quantity
                return True
        return False
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'items': [item.to_dict() for item in self.items],
            'total': self.total
        }
