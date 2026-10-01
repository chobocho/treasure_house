// 슬라이드 p2-v1-nothrows — throws 절은 문법에 없다, C# 1.0
using System.IO;

class Config
{
    public static string Load(string path) throws IOException
    {
        return File.ReadAllText(path);
    }
}

class App
{
    static void Main() { }
}
