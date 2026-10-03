// 슬라이드 p11-v10-globalusing — using 없는 파일 둘, C# 10.0
class App
{
    static void Main()
    {
        var sb = new StringBuilder("global");
        Console.WriteLine(Report.Add(sb, " using"));
    }
}
