// 슬라이드 p4-v3-et-opaque — 트리 안의 대리자는 열어 볼 수 없다, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static bool IsAdult(int age) { return age >= 18; }

    static void Main()
    {
        Func<int, bool> adult = a => a >= 18;

        Expression<Func<int, bool>> inline = a => a >= 18;
        Expression<Func<int, bool>> method = a => IsAdult(a);
        Expression<Func<int, bool>> viaVar = a => adult(a);

        Console.WriteLine(inline);
        Console.WriteLine(method);
        Console.WriteLine(viaVar);
        Console.WriteLine(viaVar.Body.NodeType);
    }
}
