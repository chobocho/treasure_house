// 슬라이드 p10-v9-patterns — 관계 패턴, C# 9.0
using System;

class App
{
    // the proposal's LifeStageAtAge, shortened
    static string Stage(int age) => age switch
    {
        < 0 => "prenatal",
        < 2 => "infant",
        < 12 => "child",
        < 20 => "adolescent",
        < 65 => "adult",
        _ => "late adult",
    };

    static void Main()
    {
        foreach (int a in new[] { -1, 0, 2, 11, 12, 64, 65 })
            Console.WriteLine(a + " " + Stage(a));
    }
}
