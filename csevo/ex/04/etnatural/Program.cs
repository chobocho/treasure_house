// 슬라이드 p4-v3-et-natural — 형식을 적지 않은 식 트리, C# 10
using System;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        LambdaExpression parse = (string s) => int.Parse(s);
        Expression any = (int x) => x * 2;

        Console.WriteLine(parse.Type);
        Console.WriteLine(any.Type);
    }
}
