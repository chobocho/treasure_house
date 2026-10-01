// 슬라이드 p4-v3-et-newobj — 식 트리는 평가마다 새로, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static Expression<Func<int, int>> Tree() { return x => x + 1; }

    static Func<int, int> Code() { return x => x + 1; }

    static void Main()
    {
        Console.WriteLine("same tree object:     "
                          + object.ReferenceEquals(Tree(), Tree()));
        Console.WriteLine("same delegate object: "
                          + object.ReferenceEquals(Code(), Code()));
    }
}
