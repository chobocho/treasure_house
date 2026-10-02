// 슬라이드 p8-v7-locfn-name — 지역 함수는 숨은 이름의 메서드, C# 7.0
using System;
using System.Linq;
using System.Reflection;

class App
{
    static void Main()
    {
        int k = 100;
        Console.WriteLine(Where());
        Console.WriteLine(Fact(5) + " " + Add(1));

        string Where() => MethodBase.GetCurrentMethod().Name;
        int Fact(int n) => n <= 1 ? 1 : n * Fact(n - 1);
        int Add(int v) => v + k;                // captures k

        var hidden = typeof(App)
            .GetMethods(BindingFlags.NonPublic | BindingFlags.Static)
            .Where(m => m.Name.Contains("g__"))
            .OrderBy(m => m.Name);
        foreach (var m in hidden)
            Console.WriteLine(m.Name + "(" + string.Join(", ",
                m.GetParameters().Select(p => p.ParameterType.Name))
                + ")");
    }
}
