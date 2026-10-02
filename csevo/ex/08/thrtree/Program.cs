// 슬라이드 p8-v7-throw-tree — 식 트리 안의 throw 식, C# 7.0
using System;
using System.Linq.Expressions;

class App
{
    static void Main()
    {
        Func<string, string> f =
            s => s ?? throw new ArgumentException();   // a delegate: ok
        Expression<Func<string, string>> e =
            s => s ?? throw new ArgumentException();
    }
}
