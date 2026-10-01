// 슬라이드 p4-v3-lambda-tree — 같은 람다, 대리자 또는 데이터, C# 3.0
using System;
using System.Linq.Expressions;

class App
{
    static void Main()
    {
        Func<int, int> code = x => x + 1;
        Expression<Func<int, int>> data = x => x + 1;

        Console.WriteLine(code(1));
        Console.WriteLine(data);
        Console.WriteLine(data.Body.NodeType);
    }
}
