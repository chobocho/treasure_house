// 슬라이드 p11-v10-gu-kinds — 정적 멤버와 별칭을 다른 파일에서, C# 10.0
class App
{
    static void Main()
    {
        var xs = new IntList { 3, -4 };
        Console.WriteLine(Max(Abs(xs[0]), Abs(xs[1])));
        Console.WriteLine(Env.NewLine.Length);
    }
}
