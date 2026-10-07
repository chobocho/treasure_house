// 슬라이드 p15-v14-xm-op-rules — 확장 연산자가 거절되는 자리, C# 14
using System;

class Money { public decimal Amount; }

static class Ops
{
    extension(Money)
    {
        public static Money operator -(Money m) =>
            new Money { Amount = -m.Amount };
#if UNRELATED
        public static int operator *(int a, int b) => a - b;
#elif CONV
        public static implicit operator decimal(Money m) => m.Amount;
#elif INST
        public Money operator +(Money a, Money b) => a;
#elif PAIR
        public static bool operator ==(Money a, Money b) => true;
#endif
    }

    extension(int)                         // same as a predefined one
    {
        public static int operator +(int a, int b) => a - b;
    }
}

class Program
{
    static void Main()
    {
        var m = new Money { Amount = 5m };
        Console.WriteLine((-m).Amount);
        Console.WriteLine((1 + 2) + " " + Ops.op_Addition(1, 2));
    }
}
