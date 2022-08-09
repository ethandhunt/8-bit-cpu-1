%define &&add_test {$3:30201 + $4:201
%define &&sub_test {$3:30201 - $4:201
%define &&mul_test {$3:30201 * $4:201
%define &&div_test {$3:30201 / $4:201
%define &&mod_test {$3:30201 % $4:201
%define &&and_test {{$3 == {$4 - $1}} &= {$3 != $4}}

%macro test a b
{a+b
%end
