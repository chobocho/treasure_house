// 슬라이드 p15-v14-xm-expr — 식 트리 안의 확장 멤버, C# 14
using System;
using System.Linq.Expressions;

class Money { public decimal Amount; }

static class Ext
{
    extension(string s)
    {
        public int Words => s.Split(' ').Length;
        public string Twice() => s + s;
    }

    extension(Money)
    {
        public static Money operator +(Money a, Money b) =>
            new Money { Amount = a.Amount + b.Amount };
    }
}

class Program
{
    static void Main()
    {
        Expression<Func<string, string>> e2 = s => s.Twice();
        Expression<Func<Money, Money>> e3 = m => m + m;
        Console.WriteLine(e2 + " | " + e2.Compile()("ab"));
        var add = (BinaryExpression)e3.Body;
        Console.WriteLine(e3 + " | " + add.Method);
        var two = new Money { Amount = 2 };
        Console.WriteLine(e3.Compile()(two).Amount);
#if PROP
        Expression<Func<string, int>> e1 = s => s.Words;
#endif
    }
}
