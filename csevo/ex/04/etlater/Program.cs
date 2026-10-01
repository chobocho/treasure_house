// 슬라이드 p4-v3-et-later — 뒤 버전의 문법과 식 트리, C# 14
using System;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        Expression<Func<string, int?>> a = s => s?.Length;
        Expression<Func<int, string>> b = x => $"#{x}";
        Expression<Func<int, (int, int)>> c = x => (x, x);
        Expression<Func<object, bool>> d = o => o is int n;
        Expression<Func<string, string>> e =
            s => s ?? throw new Exception();
        Expression<Func<int, int>> f = x => x switch { 0 => 1, _ => 2 };
        Expression<Func<int[], int>> g = xs => xs[^1];
    }
}
