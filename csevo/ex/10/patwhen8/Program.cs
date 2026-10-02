// 슬라이드 p10-v9-pat-before — C# 8.0 의 when 가드로 쓴 같은 표, C# 8.0
using System;

class App
{
    static string Stage(int age) => age switch
    {
        int a when a < 0 => "prenatal",
        int a when a < 2 => "infant",
        int a when a < 12 => "child",
        int a when a < 20 => "adolescent",
        int a when a < 65 => "adult",
        _ => "late adult",
    };

    static void Main()
    {
        foreach (int a in new[] { -1, 0, 2, 11, 12, 64, 65 })
            Console.WriteLine(a + " " + Stage(a));
    }
}
