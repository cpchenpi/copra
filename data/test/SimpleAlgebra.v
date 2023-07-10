Inductive algb : Set := 
e : algb
| t : algb.

Definition algb_eq (x y : algb) : bool :=
match x, y with
| e, e => true
| t, t => true
| _, _ => false
end.

Definition algb_add (a b : algb) : algb :=
match a, b with
| e, _ => b
| _, e => a
| t, t => e
end.

Definition algb_mul (a b : algb) : algb :=
match a, b with
| e, _ => e
| _, e => e
| t, t => t
end.

Fixpoint algb_mul_scalar (b : nat) (a : algb) : algb :=
match b, a with
| 0, _ => e
| S b', _ => algb_add a (algb_mul_scalar b' a)
end.

Theorem algb_nat_zero : forall a, a 
+ 0 = a.
Proof.
    intros.
    induction a.
    simpl.
    reflexivity.
    simpl.
    rewrite IHa.
    reflexivity.
Qed.

Theorem algb_identity_sum : 
forall a, algb_add a e = a.
Proof.
    intros. 
    destruct a.
    - reflexivity.
    - reflexivity.
Qed.

(* Theorem algb_add_comm : 
forall a b, algb_add a b = algb_add b a.
Proof.
    intros.
    destruct a.
    destruct b.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
    destruct b.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
Qed. *)

Theorem algb_add_comm : 
forall a b, algb_add a b = algb_add b a.
Proof.
unfold algb_add; intros; destruct a; destruct b; intuition.
Qed.


Print algb_add.

Theorem algb_has_identity : 
forall a, exists i, algb_add a i = a /\ algb_add i a = a.
Proof.
    intros.
    exists e.
    split.
    apply algb_identity_sum.
    simpl.
    reflexivity.
Qed.

Theorem associativity : 
forall a b c, (algb_add (algb_add a b) c) = (algb_add a (algb_add b c)).
Proof.
    intros.
    destruct a.
    destruct b.
    destruct c.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
    destruct c.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
    destruct b.
    destruct c.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
    destruct c.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
Qed.

Theorem algb_has_inverse : 
forall a, exists a', algb_add a a' = e /\ algb_add a' a = e.
Proof.
    intros.
    destruct a.
    exists e.
    split.
    apply algb_add_comm.
    auto.
    exists t.
    split.
    apply algb_add_comm.
    auto.
Qed.

Theorem algb_is_closed:
forall a b, exists c, algb_eq (algb_add a b) c = true.
Proof.
    intros.
    destruct a.
    destruct b.
    exists e.
    simpl.
    reflexivity.
    exists t.
    simpl.
    reflexivity.
    destruct b.
    exists t.
    simpl.
    reflexivity.
    exists e.
    simpl.
    reflexivity.
Qed.

Theorem algb_is_abelian_group:
forall (a b c : algb), 
(*Closure*) (exists d, algb_eq (algb_add a b) d = true) /\
(*Inverse*) (exists i, algb_add a i = e /\ algb_add i a = e) /\
(*Identity*) (exists i, algb_add a i = a /\ algb_add i a = a) /\
(*Associativity*) (algb_add (algb_add a b) c) = (algb_add a (algb_add b c)) /\
(*Commutativity*) (algb_add a b) = (algb_add b a).
Proof.
    intros.
    split.
    apply algb_is_closed.
    split.
    apply algb_has_inverse.
    split.
    apply algb_has_identity.
    split.
    apply associativity.
    apply algb_add_comm.
Qed.

(* Theorem algb_mul_is_closed:
forall a b, algb_eq (algb_mul a b) e = true \/ algb_eq (algb_mul a b) t = true.
Proof.
    intros.
    destruct a.
    left.
    simpl.
    reflexivity.
    destruct b.
    left.
    simpl.
    reflexivity.
    simpl.
    auto.
Qed. *)

Theorem algb_mul_is_closed:
forall a b, algb_eq (algb_mul a b) e = true \/ algb_eq (algb_mul a b) t = true.
Proof.
    intros; unfold algb_mul, algb_eq; destruct a; destruct b; auto.
Qed.


Theorem algb_mul_comm : 
forall a b, algb_mul a b = algb_mul b a.
Proof.
    intros.
    destruct a.
    destruct b.
    simpl.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
    destruct b.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
Qed.

Theorem algb_mul_assoc : 
forall a b c, algb_mul (algb_mul a b) c = algb_mul a (algb_mul b c).
Proof.
    intros.
    destruct a.
    destruct b.
    destruct c.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
    destruct c.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
    destruct b.
    destruct c.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
    destruct c.
    simpl.
    reflexivity.
    simpl.
    reflexivity.
Qed.

Theorem algb_mul_add_distr : 
forall a b c, algb_mul a (algb_add b c) = algb_add (algb_mul a b) (algb_mul a c).
Proof.
    intros.
    destruct a.
    destruct b.
    destruct c.
    { simpl. reflexivity. }
    { simpl. reflexivity. }
    * destruct c.
       ** simpl.
        - reflexivity.
       ** simpl.
        + reflexivity.
    * destruct b.
       ** destruct c.
          ++++ simpl.
            +++++ reflexivity.
          ++++ simpl.
            +++++ reflexivity.
        ** destruct c.
    { simpl. reflexivity. }
    { simpl. reflexivity. }
Qed.

Theorem algb_mul_add_distr1 : 
forall a b c, algb_mul a (algb_add b c) = algb_add (algb_mul a b) (algb_mul a c).
Proof.
    intros; unfold algb_mul, algb_add; intros.
    destruct a; auto; destruct b; auto.
    destruct c; intuition congruence.
Qed.