// 슬라이드 p11-v10-globalusing — 다른 파일도 지시문을 본다, C# 10.0
static class Report
{
    public static string Add(StringBuilder sb, string s) =>
        sb.Append(s).Append(" @ ").Append(Environment.Version.Major)
          .ToString();
}
