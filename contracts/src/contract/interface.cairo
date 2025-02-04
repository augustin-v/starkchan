#[starknet::interface]
pub trait IHelloStarkChan<TContractState> {
    fn get_id(self: @TContractState) -> usize;
    fn verify_cup_size_with_cup(ref self: TContractState, input: u8);
    fn verify_cup_size_with_hash(ref self: TContractState, input: felt252);
    fn get_cup_hash(self: @TContractState) -> felt252;
    fn is_winner(ref self: TContractState) -> bool;
}