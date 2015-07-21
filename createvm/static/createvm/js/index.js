$(function() {
	
	/*选择CPU*/
	$(".hz-cpu .unit").click(function(){
		
		$(this).addClass("current");
		$(this).siblings(".unit").removeClass("current");

		$("#hz-cpu").val($(this).attr("tocpu"));
		
		//根据cpu显示内存
		$(".hz-memory").hide();
		var showm = $(this).attr("showm");
		$("#"+showm).show();
		var memoryid = $("#"+showm).find(".current").attr("tomemory");
		$("#hz-memory").val(memoryid);
	
	});
	/*选择CPU*/

	/*选择内存*/
	$(".hz-memory .unit").click(function(){
		
		$(this).addClass("current");
		$(this).siblings(".unit").removeClass("current");

		$("#hz-memory").val($(this).attr("tomemory"));
	
	});
	/*选择内存*/

	/*选择系统*/
	$("#sys-change").change(function(){
		
		var selected = $(this).children('option:selected').val();
		var toversion = $(this).children('option:selected').attr("toversion");

		$(".version-change").removeClass("active-change");
		$("#"+toversion).addClass("active-change");


	});
	/*选择系统*/
	

});