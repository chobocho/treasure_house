// 슬라이드 p10-v9-rec-gatemsg — 'records' 거절이 나오는 곳, C# 9.0
class App
{
    public int X { get; set; }

    static void Main()
    {
        App a = new App();
        App b = a with { X = 2 };
    }
}
